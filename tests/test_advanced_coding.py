"""
Tests for Advanced Coding XBlock
"""

import json
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

from advanced_coding import AdvancedCodingXBlock


class TestAdvancedCodingXBlock(unittest.TestCase):
    """Test cases for AdvancedCodingXBlock"""

    def setUp(self):
        """Set up test environment"""
        self.runtime = Mock()
        self.xblock = AdvancedCodingXBlock(self.runtime, field_data={}, scope_ids=Mock())
        
        # Mock scope_ids for user identification
        self.xblock.scope_ids.user_id = 'test_user_123'
        self.xblock.scope_ids.usage_id = 'test_usage_456'

    def test_initialization(self):
        """Test XBlock initialization"""
        self.assertIsNotNone(self.xblock)
        self.assertEqual(self.xblock.display_name, "Advanced Coding Assessment")
        self.assertIsInstance(self.xblock.supported_languages, dict)
        self.assertIn('python', self.xblock.supported_languages)

    def test_initialize_student_files(self):
        """Test student files initialization"""
        # Clear existing files
        self.xblock.student_files = {}
        self.xblock._initialize_student_files()
        
        self.assertIsNotNone(self.xblock.student_files)
        self.assertTrue(len(self.xblock.student_files) > 0)
        self.assertIn('main.py', self.xblock.student_files)
        
        main_file = self.xblock.student_files['main.py']
        self.assertIn('content', main_file)
        self.assertIn('language', main_file)
        self.assertEqual(main_file['language'], 'python')

    def test_validate_file_name(self):
        """Test file name validation"""
        # Valid file names
        valid, msg = self.xblock.validate_file_name('test.py')
        self.assertTrue(valid)
        self.assertEqual(msg, "")
        
        valid, msg = self.xblock.validate_file_name('solution.java')
        self.assertTrue(valid)
        
        # Invalid file names
        valid, msg = self.xblock.validate_file_name('')
        self.assertFalse(valid)
        
        valid, msg = self.xblock.validate_file_name('test')
        self.assertFalse(valid)
        
        valid, msg = self.xblock.validate_file_name('test.exe')
        self.assertFalse(valid)
        
        valid, msg = self.xblock.validate_file_name('test..py')
        self.assertFalse(valid)

    def test_validate_file_content(self):
        """Test file content validation"""
        # Valid content
        valid, msg = self.xblock.validate_file_content('print("Hello, World!")')
        self.assertTrue(valid)
        
        # Empty content (should be valid)
        valid, msg = self.xblock.validate_file_content('')
        self.assertTrue(valid)
        
        # Content too large
        large_content = 'x' * (self.xblock.max_file_size + 1)
        valid, msg = self.xblock.validate_file_content(large_content)
        self.assertFalse(valid)

    def test_save_file_handler(self):
        """Test save file handler"""
        data = {
            'filename': 'test.py',
            'content': 'print("Hello from test!")',
            'language': 'python'
        }
        
        response = self.xblock.save_file(data)
        
        self.assertIsInstance(response, dict)
        self.assertTrue(response['success'])
        self.assertIn('test.py', self.xblock.student_files)
        
        saved_file = self.xblock.student_files['test.py']
        self.assertEqual(saved_file['content'], 'print("Hello from test!")')
        self.assertEqual(saved_file['language'], 'python')

    def test_delete_file_handler(self):
        """Test delete file handler"""
        # Add multiple files first
        self.xblock.student_files = {
            'main.py': {'content': 'print("main")', 'language': 'python'},
            'utils.py': {'content': 'print("utils")', 'language': 'python'}
        }
        
        data = {'filename': 'utils.py'}
        response = self.xblock.delete_file(data)
        
        self.assertTrue(response['success'])
        self.assertNotIn('utils.py', self.xblock.student_files)
        self.assertIn('main.py', self.xblock.student_files)

    def test_delete_last_file_fails(self):
        """Test that deleting the last file fails"""
        self.xblock.student_files = {
            'main.py': {'content': 'print("main")', 'language': 'python'}
        }
        
        data = {'filename': 'main.py'}
        response = self.xblock.delete_file(data)
        
        self.assertFalse(response['success'])
        self.assertIn('Cannot delete the last file', response['error'])

    def test_rename_file_handler(self):
        """Test rename file handler"""
        self.xblock.student_files = {
            'old_name.py': {'content': 'print("test")', 'language': 'python'}
        }
        self.xblock.active_file = 'old_name.py'
        
        data = {
            'old_filename': 'old_name.py',
            'new_filename': 'new_name.py'
        }
        
        response = self.xblock.rename_file(data)
        
        self.assertTrue(response['success'])
        self.assertNotIn('old_name.py', self.xblock.student_files)
        self.assertIn('new_name.py', self.xblock.student_files)
        self.assertEqual(self.xblock.active_file, 'new_name.py')

    @patch('advanced_coding.requests.post')
    def test_execute_code_judge0_success(self, mock_post):
        """Test successful Judge0 code execution"""
        # Mock Judge0 submission response
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {'token': 'test_token_123'}
        
        # Mock Judge0 result response
        with patch('advanced_coding.requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                'status': {'id': 3, 'description': 'Accepted'},
                'stdout': 'Hello, World!\n',
                'stderr': '',
                'time': '0.001',
                'memory': 1024
            }
            
            # Configure API settings
            self.xblock.judge0_api_key = 'test_api_key'
            self.xblock.judge0_api_host = 'test_host'
            
            result = self.xblock._execute_code_judge0('print("Hello, World!")', 71, '')
            
            self.assertTrue(result['success'])
            self.assertEqual(result['stdout'], 'Hello, World!\n')
            self.assertEqual(result['status']['description'], 'Accepted')

    @patch('advanced_coding.requests.post')
    def test_execute_code_judge0_failure(self, mock_post):
        """Test Judge0 API failure"""
        mock_post.side_effect = Exception('API Error')
        
        self.xblock.judge0_api_key = 'test_api_key'
        result = self.xblock._execute_code_judge0('print("Hello")', 71, '')
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)

    def test_run_code_handler(self):
        """Test run code handler"""
        # Set up file
        self.xblock.student_files = {
            'test.py': {'content': 'print("Hello")', 'language': 'python'}
        }
        self.xblock.active_file = 'test.py'
        
        with patch.object(self.xblock, '_execute_code_judge0') as mock_execute:
            mock_execute.return_value = {
                'success': True,
                'stdout': 'Hello\n',
                'stderr': '',
                'status': {'description': 'Accepted'}
            }
            
            data = {'filename': 'test.py', 'input': ''}
            response = self.xblock.run_code(data)
            
            self.assertTrue(response['success'])
            self.assertEqual(response['output'], 'Hello\n')

    def test_submit_solution_handler(self):
        """Test solution submission"""
        # Set up test case
        self.xblock.test_cases = [
            {
                'id': 'test_1',
                'name': 'Test Case 1',
                'input': '',
                'expected_output': 'Hello\n',
                'is_public': True,
                'points': 10,
                'timeout': 2.0
            }
        ]
        
        # Set up student file
        self.xblock.student_files = {
            'main.py': {'content': 'print("Hello")', 'language': 'python'}
        }
        
        with patch.object(self.xblock, '_execute_code_judge0') as mock_execute:
            mock_execute.return_value = {
                'success': True,
                'stdout': 'Hello\n',
                'stderr': '',
                'status': {'description': 'Accepted'}
            }
            
            with patch.object(self.xblock, '_publish_grade') as mock_publish:
                data = {'main_file': 'main.py'}
                response = self.xblock.submit_solution(data)
                
                self.assertTrue(response['success'])
                self.assertEqual(response['passed_tests'], 1)
                self.assertEqual(response['total_tests'], 1)
                self.assertGreater(response['score'], 0)
                
                # Check that grade was published
                mock_publish.assert_called_once()

    def test_get_student_data_handler(self):
        """Test get student data handler"""
        response = self.xblock.get_student_data({})
        
        self.assertIn('files', response)
        self.assertIn('active_file', response)
        self.assertIn('current_language', response)
        self.assertIn('current_score', response)
        self.assertIn('supported_languages', response)

    def test_validate_xblock_configuration(self):
        """Test XBlock configuration validation"""
        validation = self.xblock.validate()
        
        # Should have warnings about missing API key
        warnings = [msg for msg in validation.messages if msg.type == validation.WARNING]
        self.assertTrue(any('Judge0 API key' in str(msg.text) for msg in warnings))

    def test_score_calculation(self):
        """Test score calculation logic"""
        # Set up test cases with different point values
        self.xblock.test_cases = [
            {'points': 10, 'expected_output': 'correct'},
            {'points': 20, 'expected_output': 'also_correct'}
        ]
        self.xblock.max_score = 100.0
        
        # All tests pass
        with patch.object(self.xblock, '_execute_code_judge0') as mock_execute:
            mock_execute.return_value = {
                'success': True,
                'stdout': 'correct',
                'stderr': ''
            }
            
            # First call returns 'correct', second call returns 'also_correct'
            mock_execute.side_effect = [
                {'success': True, 'stdout': 'correct', 'stderr': ''},
                {'success': True, 'stdout': 'also_correct', 'stderr': ''}
            ]
            
            self.xblock.student_files = {
                'main.py': {'content': 'print("test")', 'language': 'python'}
            }
            
            with patch.object(self.xblock, '_publish_grade'):
                response = self.xblock.submit_solution({'main_file': 'main.py'})
                
                # Should get full score (30 points = 100% of max)
                self.assertEqual(response['score'], self.xblock.max_score)

    def test_markdown_processing(self):
        """Test markdown processing in problem statement"""
        # This would test markdown rendering if implemented
        self.xblock.problem_statement = "# Test Problem\n\nThis is a **bold** statement."
        
        # In a real implementation, you'd test the markdown processing here
        # For now, just verify the field exists and can be set
        self.assertEqual(self.xblock.problem_statement, "# Test Problem\n\nThis is a **bold** statement.")


class TestSecurityFeatures(unittest.TestCase):
    """Test security-related functionality"""

    def setUp(self):
        self.runtime = Mock()
        self.xblock = AdvancedCodingXBlock(self.runtime, field_data={}, scope_ids=Mock())

    def test_dangerous_code_detection(self):
        """Test detection of potentially dangerous code patterns"""
        dangerous_code = """
import os
os.system('rm -rf /')
"""
        
        valid, msg = self.xblock.validate_file_content(dangerous_code)
        # The current implementation logs warnings but still allows the code
        # In a production environment, you might want stricter validation
        self.assertTrue(valid)  # Current behavior - adjust based on security needs

    def test_path_traversal_protection(self):
        """Test protection against path traversal attacks"""
        malicious_names = [
            '../../../etc/passwd',
            '..\\..\\windows\\system32\\config\\sam',
            'test/../../secret.py'
        ]
        
        for name in malicious_names:
            valid, msg = self.xblock.validate_file_name(name)
            self.assertFalse(valid, f"Path traversal attack not blocked: {name}")

    def test_file_size_limits(self):
        """Test file size limitation enforcement"""
        # Test with content that exceeds the limit
        oversized_content = 'x' * (self.xblock.max_file_size + 1)
        
        data = {
            'filename': 'large_file.py',
            'content': oversized_content,
            'language': 'python'
        }
        
        response = self.xblock.save_file(data)
        self.assertFalse(response['success'])
        self.assertIn('File size exceeds limit', response['error'])


if __name__ == '__main__':
    unittest.main()
