"""
Advanced Coding XBlock - A comprehensive coding assessment platform for Open edX
Integrates Monaco Editor with Judge0 API for multi-file project support
"""

import json
import logging
import hashlib
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urljoin

import requests
import bleach
from web_fragments.fragment import Fragment
from xblock.core import XBlock
from xblock.fields import Scope, String, Integer, Float, Dict as DictField, List as ListField, Boolean
from xblock.validation import ValidationMessage
from xblockutils.studio_editable import StudioEditableXBlockMixin
from xblockutils.resources import ResourceLoader

logger = logging.getLogger(__name__)
loader = ResourceLoader(__name__)


class AdvancedCodingXBlock(StudioEditableXBlockMixin, XBlock):
    """
    Advanced Coding Assessment XBlock with Monaco Editor and Judge0 integration.
    
    Features:
    - Multi-file project support with tabbed interface
    - Monaco Editor with syntax highlighting for multiple languages
    - Judge0 API integration for secure code execution
    - Automated testing with public and hidden test cases
    - Real-time feedback and grading
    - File management (create, delete, rename)
    - Security features and input validation
    """

    # Display name for the XBlock
    display_name = String(
        display_name="Display Name",
        help="Display name for this component",
        default="Advanced Coding Assessment",
        scope=Scope.settings
    )

    # Problem statement and description
    problem_statement = String(
        display_name="Problem Statement",
        help="The coding problem description in Markdown format",
        default="# Coding Problem\n\nWrite a program that solves the given problem.",
        multiline_editor=True,
        scope=Scope.content
    )

    # Supported programming languages configuration
    supported_languages = DictField(
        display_name="Supported Languages",
        help="Dictionary of supported programming languages with Judge0 language IDs",
        default={
            "python": {"id": 71, "name": "Python 3", "extension": "py", "template": "# Write your Python code here\nprint('Hello, World!')"},
            "java": {"id": 62, "name": "Java", "extension": "java", "template": "public class Main {\n    public static void main(String[] args) {\n        System.out.println(\"Hello, World!\");\n    }\n}"},
            "cpp": {"id": 76, "name": "C++", "extension": "cpp", "template": "#include <iostream>\nusing namespace std;\n\nint main() {\n    cout << \"Hello, World!\" << endl;\n    return 0;\n}"},
            "javascript": {"id": 63, "name": "JavaScript", "extension": "js", "template": "// Write your JavaScript code here\nconsole.log('Hello, World!');"},
            "c": {"id": 75, "name": "C", "extension": "c", "template": "#include <stdio.h>\n\nint main() {\n    printf(\"Hello, World!\\n\");\n    return 0;\n}"}
        },
        scope=Scope.content
    )

    # Default programming language
    default_language = String(
        display_name="Default Language",
        help="Default programming language for new projects",
        default="python",
        scope=Scope.content
    )

    # Judge0 API configuration
    judge0_api_url = String(
        display_name="Judge0 API URL",
        help="Judge0 API base URL for code execution",
        default="https://judge0-ce.p.rapidapi.com",
        scope=Scope.content
    )

    judge0_api_key = String(
        display_name="Judge0 API Key",
        help="RapidAPI key for Judge0 service (keep secure)",
        default="",
        scope=Scope.content
    )

    judge0_api_host = String(
        display_name="Judge0 API Host",
        help="RapidAPI host for Judge0 service",
        default="judge0-ce.p.rapidapi.com",
        scope=Scope.content
    )

    # Test cases configuration
    test_cases = ListField(
        display_name="Test Cases",
        help="List of test cases for automated assessment",
        default=[
            {
                "id": "test_1",
                "name": "Sample Test Case",
                "input": "5 3",
                "expected_output": "8",
                "is_public": True,
                "points": 10,
                "timeout": 2.0
            }
        ],
        scope=Scope.content
    )

    # Grading configuration
    max_score = Float(
        display_name="Maximum Score",
        help="Maximum score for this problem",
        default=100.0,
        scope=Scope.content
    )

    # Time and resource limits
    execution_time_limit = Float(
        display_name="Execution Time Limit (seconds)",
        help="Maximum execution time for code submissions",
        default=5.0,
        scope=Scope.content
    )

    memory_limit = Integer(
        display_name="Memory Limit (KB)",
        help="Maximum memory usage for code execution",
        default=128000,
        scope=Scope.content
    )

    # File management settings
    max_files = Integer(
        display_name="Maximum Files",
        help="Maximum number of files allowed per project",
        default=10,
        scope=Scope.content
    )

    max_file_size = Integer(
        display_name="Maximum File Size (bytes)",
        help="Maximum size per file in bytes",
        default=100000,
        scope=Scope.content
    )

    allowed_file_extensions = ListField(
        display_name="Allowed File Extensions",
        help="List of allowed file extensions",
        default=[".py", ".java", ".cpp", ".c", ".js", ".h", ".hpp", ".txt", ".md"],
        scope=Scope.content
    )

    # Student data fields
    student_files = DictField(
        display_name="Student Files",
        help="Student's code files and content",
        default={},
        scope=Scope.user_state
    )

    current_language = String(
        display_name="Current Language",
        help="Currently selected programming language",
        default="python",
        scope=Scope.user_state
    )

    active_file = String(
        display_name="Active File",
        help="Currently active/selected file",
        default="main.py",
        scope=Scope.user_state
    )

    # Submission and grading data
    submissions = ListField(
        display_name="Submissions",
        help="List of student submissions with results",
        default=[],
        scope=Scope.user_state
    )

    current_score = Float(
        display_name="Current Score",
        help="Student's current score for this problem",
        default=0.0,
        scope=Scope.user_state
    )

    best_score = Float(
        display_name="Best Score",
        help="Student's best score achieved",
        default=0.0,
        scope=Scope.user_state
    )

    submission_count = Integer(
        display_name="Submission Count",
        help="Number of submissions made by student",
        default=0,
        scope=Scope.user_state
    )

    last_submission_time = String(
        display_name="Last Submission Time",
        help="Timestamp of last submission",
        default="",
        scope=Scope.user_state
    )

    # Studio editor configuration
    editable_fields = (
        'display_name', 'problem_statement', 'supported_languages', 'default_language',
        'judge0_api_url', 'judge0_api_key', 'judge0_api_host', 'test_cases',
        'max_score', 'execution_time_limit', 'memory_limit', 'max_files',
        'max_file_size', 'allowed_file_extensions'
    )

    def resource_string(self, path):
        """Handy helper for getting resources from our kit."""
        data = loader.load_unicode(path)
        return data

    def student_view(self, context=None):
        """
        Create a fragment used to display the XBlock to a student.
        """
        # Initialize student files if empty
        if not self.student_files:
            self._initialize_student_files()

        # Prepare context for template
        template_context = {
            'xblock': self,
            'student_files': self.student_files,
            'supported_languages': self.supported_languages,
            'current_language': self.current_language,
            'active_file': self.active_file,
            'problem_statement': self.problem_statement,
            'test_cases': [tc for tc in self.test_cases if tc.get('is_public', True)],
            'max_score': self.max_score,
            'current_score': self.current_score,
            'best_score': self.best_score,
            'submission_count': self.submission_count,
        }

        # Load HTML template
        html = loader.render_django_template('static/html/advanced_coding.html', template_context)
        
        # Create fragment
        frag = Fragment(html)
        
        # Add CSS
        frag.add_css(self.resource_string("static/css/advanced_coding.css"))
        
        # Add JavaScript
        frag.add_javascript(self.resource_string("static/js/advanced_coding.js"))
        
        # Initialize JavaScript
        frag.initialize_js('AdvancedCodingXBlock')
        
        return frag

    def studio_view(self, context=None):
        """
        Create a fragment used to display the edit form in the Studio.
        """
        frag = super().studio_view(context)
        frag.add_css(self.resource_string("static/css/advanced_coding_studio.css"))
        frag.add_javascript(self.resource_string("static/js/advanced_coding_studio.js"))
        frag.initialize_js('AdvancedCodingStudioXBlock')
        return frag

    def _initialize_student_files(self):
        """Initialize student files with default template based on selected language."""
        lang_config = self.supported_languages.get(self.default_language, self.supported_languages['python'])
        template_code = lang_config.get('template', '// Write your code here')
        extension = lang_config.get('extension', 'py')
        
        self.student_files = {
            f"main.{extension}": {
                'content': template_code,
                'language': self.default_language,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'modified_at': datetime.now(timezone.utc).isoformat()
            }
        }
        self.active_file = f"main.{extension}"
        self.current_language = self.default_language

    def validate_file_name(self, filename: str) -> Tuple[bool, str]:
        """Validate file name for security and format requirements."""
        if not filename:
            return False, "File name cannot be empty"
        
        if len(filename) > 100:
            return False, "File name too long (max 100 characters)"
        
        # Check for dangerous characters
        dangerous_chars = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in dangerous_chars:
            if char in filename:
                return False, f"File name contains invalid character: {char}"
        
        # Check file extension
        if '.' not in filename:
            return False, "File name must have an extension"
        
        extension = '.' + filename.split('.')[-1].lower()
        if extension not in self.allowed_file_extensions:
            return False, f"File extension {extension} not allowed"
        
        return True, ""

    def validate_file_content(self, content: str) -> Tuple[bool, str]:
        """Validate file content for security and size requirements."""
        if len(content.encode('utf-8')) > self.max_file_size:
            return False, f"File size exceeds limit of {self.max_file_size} bytes"
        
        # Basic content filtering - block obviously dangerous patterns
        dangerous_patterns = [
            'import os', 'import sys', 'import subprocess', '__import__',
            'eval(', 'exec(', 'compile(', 'open(', 'file(',
            'socket', 'urllib', 'requests', 'http'
        ]
        
        content_lower = content.lower()
        for pattern in dangerous_patterns:
            if pattern in content_lower:
                logger.warning(f"Potentially dangerous pattern detected: {pattern}")
                # Note: In production, you might want to be more strict here
        
        return True, ""

    @XBlock.json_handler
    def save_file(self, data, suffix=''):
        """Save or update a file in the student's project."""
        try:
            filename = data.get('filename', '').strip()
            content = data.get('content', '')
            language = data.get('language', self.current_language)
            
            # Validate inputs
            is_valid, error_msg = self.validate_file_name(filename)
            if not is_valid:
                return {'success': False, 'error': error_msg}
            
            is_valid, error_msg = self.validate_file_content(content)
            if not is_valid:
                return {'success': False, 'error': error_msg}
            
            # Check file count limit
            if filename not in self.student_files and len(self.student_files) >= self.max_files:
                return {'success': False, 'error': f'Maximum number of files ({self.max_files}) reached'}
            
            # Clean content
            content = bleach.clean(content, tags=[], attributes={}, strip=True)
            
            # Save file
            now = datetime.now(timezone.utc).isoformat()
            if filename in self.student_files:
                self.student_files[filename]['content'] = content
                self.student_files[filename]['language'] = language
                self.student_files[filename]['modified_at'] = now
            else:
                self.student_files[filename] = {
                    'content': content,
                    'language': language,
                    'created_at': now,
                    'modified_at': now
                }
            
            # Update active file
            self.active_file = filename
            self.current_language = language
            
            return {'success': True, 'message': f'File {filename} saved successfully'}
            
        except Exception as e:
            logger.error(f"Error saving file: {str(e)}")
            return {'success': False, 'error': 'Failed to save file'}

    @XBlock.json_handler
    def delete_file(self, data, suffix=''):
        """Delete a file from the student's project."""
        try:
            filename = data.get('filename', '').strip()
            
            if not filename:
                return {'success': False, 'error': 'File name required'}
            
            if filename not in self.student_files:
                return {'success': False, 'error': 'File not found'}
            
            if len(self.student_files) <= 1:
                return {'success': False, 'error': 'Cannot delete the last file'}
            
            # Delete file
            del self.student_files[filename]
            
            # Update active file if necessary
            if self.active_file == filename:
                self.active_file = list(self.student_files.keys())[0]
            
            return {'success': True, 'message': f'File {filename} deleted successfully'}
            
        except Exception as e:
            logger.error(f"Error deleting file: {str(e)}")
            return {'success': False, 'error': 'Failed to delete file'}

    @XBlock.json_handler
    def rename_file(self, data, suffix=''):
        """Rename a file in the student's project."""
        try:
            old_filename = data.get('old_filename', '').strip()
            new_filename = data.get('new_filename', '').strip()
            
            if not old_filename or not new_filename:
                return {'success': False, 'error': 'Both old and new file names required'}
            
            if old_filename not in self.student_files:
                return {'success': False, 'error': 'Original file not found'}
            
            if new_filename in self.student_files:
                return {'success': False, 'error': 'File with new name already exists'}
            
            # Validate new filename
            is_valid, error_msg = self.validate_file_name(new_filename)
            if not is_valid:
                return {'success': False, 'error': error_msg}
            
            # Rename file
            file_data = self.student_files[old_filename].copy()
            file_data['modified_at'] = datetime.now(timezone.utc).isoformat()
            
            del self.student_files[old_filename]
            self.student_files[new_filename] = file_data
            
            # Update active file if necessary
            if self.active_file == old_filename:
                self.active_file = new_filename
            
            return {'success': True, 'message': f'File renamed from {old_filename} to {new_filename}'}
            
        except Exception as e:
            logger.error(f"Error renaming file: {str(e)}")
            return {'success': False, 'error': 'Failed to rename file'}

    @XBlock.json_handler
    def run_code(self, data, suffix=''):
        """Execute student code using Judge0 API."""
        try:
            filename = data.get('filename', self.active_file)
            custom_input = data.get('input', '')
            
            if filename not in self.student_files:
                return {'success': False, 'error': 'File not found'}
            
            file_data = self.student_files[filename]
            language = file_data.get('language', self.current_language)
            code = file_data.get('content', '')
            
            if not code.strip():
                return {'success': False, 'error': 'No code to execute'}
            
            # Get language configuration
            lang_config = self.supported_languages.get(language)
            if not lang_config:
                return {'success': False, 'error': f'Unsupported language: {language}'}
            
            # Execute code
            result = self._execute_code_judge0(code, lang_config['id'], custom_input)
            
            if result['success']:
                return {
                    'success': True,
                    'output': result.get('stdout', ''),
                    'error': result.get('stderr', ''),
                    'compile_output': result.get('compile_output', ''),
                    'status': result.get('status', {}),
                    'time': result.get('time', 0),
                    'memory': result.get('memory', 0)
                }
            else:
                return {'success': False, 'error': result.get('error', 'Execution failed')}
                
        except Exception as e:
            logger.error(f"Error running code: {str(e)}")
            return {'success': False, 'error': 'Failed to execute code'}

    @XBlock.json_handler
    def submit_solution(self, data, suffix=''):
        """Submit solution and run against all test cases."""
        try:
            # Get main file or specified file
            main_file = data.get('main_file')
            if not main_file:
                # Try to find main file
                possible_mains = [f for f in self.student_files.keys() if 'main' in f.lower()]
                if possible_mains:
                    main_file = possible_mains[0]
                else:
                    main_file = list(self.student_files.keys())[0]
            
            if main_file not in self.student_files:
                return {'success': False, 'error': 'Main file not found'}
            
            file_data = self.student_files[main_file]
            language = file_data.get('language', self.current_language)
            code = file_data.get('content', '')
            
            if not code.strip():
                return {'success': False, 'error': 'No code to submit'}
            
            # Get language configuration
            lang_config = self.supported_languages.get(language)
            if not lang_config:
                return {'success': False, 'error': f'Unsupported language: {language}'}
            
            # Run all test cases
            test_results = []
            total_score = 0.0
            passed_tests = 0
            
            for test_case in self.test_cases:
                result = self._execute_code_judge0(
                    code, 
                    lang_config['id'], 
                    test_case.get('input', ''),
                    timeout=test_case.get('timeout', self.execution_time_limit)
                )
                
                if result['success']:
                    expected = test_case.get('expected_output', '').strip()
                    actual = result.get('stdout', '').strip()
                    passed = expected == actual
                    
                    if passed:
                        passed_tests += 1
                        total_score += test_case.get('points', 0)
                    
                    test_results.append({
                        'test_id': test_case.get('id', ''),
                        'name': test_case.get('name', ''),
                        'passed': passed,
                        'expected_output': expected if test_case.get('is_public', True) else '[Hidden]',
                        'actual_output': actual,
                        'points': test_case.get('points', 0),
                        'earned_points': test_case.get('points', 0) if passed else 0,
                        'execution_time': result.get('time', 0),
                        'memory_used': result.get('memory', 0),
                        'is_public': test_case.get('is_public', True)
                    })
                else:
                    test_results.append({
                        'test_id': test_case.get('id', ''),
                        'name': test_case.get('name', ''),
                        'passed': False,
                        'error': result.get('error', 'Execution failed'),
                        'points': test_case.get('points', 0),
                        'earned_points': 0,
                        'is_public': test_case.get('is_public', True)
                    })
            
            # Calculate final score
            max_possible = sum(tc.get('points', 0) for tc in self.test_cases)
            if max_possible > 0:
                score_percentage = (total_score / max_possible) * 100
                final_score = min(score_percentage * (self.max_score / 100), self.max_score)
            else:
                final_score = 0.0
            
            # Save submission
            submission = {
                'id': str(uuid.uuid4()),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'code': code,
                'main_file': main_file,
                'language': language,
                'test_results': test_results,
                'score': final_score,
                'passed_tests': passed_tests,
                'total_tests': len(self.test_cases)
            }
            
            self.submissions.append(submission)
            self.submission_count += 1
            self.current_score = final_score
            self.last_submission_time = submission['timestamp']
            
            # Update best score
            if final_score > self.best_score:
                self.best_score = final_score
            
            # Publish grade
            self._publish_grade(final_score)
            
            return {
                'success': True,
                'submission_id': submission['id'],
                'score': final_score,
                'max_score': self.max_score,
                'passed_tests': passed_tests,
                'total_tests': len(self.test_cases),
                'test_results': [tr for tr in test_results if tr.get('is_public', True)],
                'message': f'Submitted successfully! Score: {final_score:.1f}/{self.max_score}'
            }
            
        except Exception as e:
            logger.error(f"Error submitting solution: {str(e)}")
            return {'success': False, 'error': 'Failed to submit solution'}

    def _execute_code_judge0(self, code: str, language_id: int, stdin: str = "", timeout: float = None) -> Dict:
        """Execute code using Judge0 API."""
        if not self.judge0_api_key:
            return {'success': False, 'error': 'Judge0 API key not configured'}
        
        if timeout is None:
            timeout = self.execution_time_limit
        
        headers = {
            'X-RapidAPI-Key': self.judge0_api_key,
            'X-RapidAPI-Host': self.judge0_api_host,
            'Content-Type': 'application/json'
        }
        
        # Prepare submission data
        submission_data = {
            'source_code': code,
            'language_id': language_id,
            'stdin': stdin,
            'cpu_time_limit': timeout,
            'memory_limit': self.memory_limit // 1024,  # Convert to MB
            'wall_time_limit': timeout + 1,
            'compiler_options': '',
            'command_line_arguments': '',
            'redirect_stderr_to_stdout': False,
            'callback_url': '',
            'additional_files': ''
        }
        
        try:
            # Submit code for execution
            submit_url = f"{self.judge0_api_url}/submissions"
            response = requests.post(
                submit_url,
                json=submission_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code != 201:
                logger.error(f"Judge0 submission failed: {response.status_code} - {response.text}")
                return {'success': False, 'error': f'Submission failed: {response.status_code}'}
            
            submission = response.json()
            token = submission.get('token')
            
            if not token:
                return {'success': False, 'error': 'No submission token received'}
            
            # Poll for results
            max_attempts = 30
            attempt = 0
            
            while attempt < max_attempts:
                time.sleep(1)  # Wait 1 second between polls
                
                result_url = f"{self.judge0_api_url}/submissions/{token}"
                result_response = requests.get(result_url, headers=headers, timeout=10)
                
                if result_response.status_code != 200:
                    logger.error(f"Judge0 result fetch failed: {result_response.status_code}")
                    continue
                
                result = result_response.json()
                status = result.get('status', {})
                
                # Check if execution is complete
                if status.get('id') not in [1, 2]:  # 1=In Queue, 2=Processing
                    return {
                        'success': True,
                        'stdout': result.get('stdout', ''),
                        'stderr': result.get('stderr', ''),
                        'compile_output': result.get('compile_output', ''),
                        'status': status,
                        'time': result.get('time'),
                        'memory': result.get('memory'),
                        'token': token
                    }
                
                attempt += 1
            
            return {'success': False, 'error': 'Execution timeout - results not available'}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Judge0 API request failed: {str(e)}")
            return {'success': False, 'error': f'API request failed: {str(e)}'}
        except Exception as e:
            logger.error(f"Judge0 execution error: {str(e)}")
            return {'success': False, 'error': f'Execution error: {str(e)}'}

    def _publish_grade(self, score: float):
        """Publish grade to Open edX gradebook."""
        try:
            self.runtime.publish(
                self,
                'grade',
                {
                    'value': score,
                    'max_value': self.max_score,
                    'user_id': self.scope_ids.user_id
                }
            )
        except Exception as e:
            logger.error(f"Failed to publish grade: {str(e)}")

    @XBlock.json_handler
    def get_student_data(self, data, suffix=''):
        """Get current student data and state."""
        return {
            'files': self.student_files,
            'active_file': self.active_file,
            'current_language': self.current_language,
            'current_score': self.current_score,
            'best_score': self.best_score,
            'submission_count': self.submission_count,
            'supported_languages': self.supported_languages
        }

    @XBlock.json_handler
    def reset_student_data(self, data, suffix=''):
        """Reset student data (instructor only)."""
        if not self.runtime.user_is_staff:
            return {'success': False, 'error': 'Permission denied'}
        
        try:
            self._initialize_student_files()
            self.submissions = []
            self.current_score = 0.0
            self.best_score = 0.0
            self.submission_count = 0
            self.last_submission_time = ""
            
            return {'success': True, 'message': 'Student data reset successfully'}
        except Exception as e:
            logger.error(f"Error resetting student data: {str(e)}")
            return {'success': False, 'error': 'Failed to reset student data'}

    def validate(self):
        """Validate XBlock configuration."""
        validation = super().validate()
        
        # Validate Judge0 configuration
        if not self.judge0_api_key:
            validation.add(ValidationMessage(ValidationMessage.WARNING, 
                          "Judge0 API key is not configured. Code execution will not work."))
        
        # Validate test cases
        if not self.test_cases:
            validation.add(ValidationMessage(ValidationMessage.WARNING,
                          "No test cases configured. Automated grading will not work."))
        
        # Validate supported languages
        if not self.supported_languages:
            validation.add(ValidationMessage(ValidationMessage.ERROR,
                          "At least one programming language must be supported."))
        
        return validation

    @staticmethod
    def workbench_scenarios():
        """A canned scenario for display in the workbench."""
        return [
            ("AdvancedCodingXBlock",
             """<advanced_coding/>
             """),
            ("Multiple AdvancedCodingXBlock",
             """<vertical_demo>
                <advanced_coding/>
                <advanced_coding/>
                <advanced_coding/>
                </vertical_demo>
             """),
        ]
