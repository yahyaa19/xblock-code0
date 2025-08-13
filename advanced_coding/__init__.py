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
from xblock.utils.studio_editable import StudioEditableXBlockMixin
from xblock.utils.resources import ResourceLoader

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
        scope=Scope.settings
    )

    # Default programming language
    default_language = String(
        display_name="Default Language",
        help="Default programming language for new projects",
        default="python",
        scope=Scope.settings
    )

    # Judge0 API configuration
    judge0_api_url = String(
        display_name="Judge0 API URL",
        help="Judge0 API base URL for code execution",
        default="https://judge0-ce.p.rapidapi.com",
        scope=Scope.settings
    )

    judge0_api_key = String(
        display_name="Judge0 API Key",
        help="RapidAPI key for Judge0 service (keep secure)",
        default="",
        scope=Scope.settings
    )

    judge0_api_host = String(
        display_name="Judge0 API Host",
        help="RapidAPI host for Judge0 service",
        default="judge0-ce.p.rapidapi.com",
        scope=Scope.settings
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
        scope=Scope.settings
    )

    # Time and resource limits
    execution_time_limit = Float(
        display_name="Execution Time Limit (seconds)",
        help="Maximum execution time for code submissions",
        default=5.0,
        scope=Scope.settings
    )

    memory_limit = Integer(
        display_name="Memory Limit (KB)",
        help="Maximum memory usage for code execution",
        default=128000,
        scope=Scope.settings
    )

    # File management settings
    max_files = Integer(
        display_name="Maximum Files",
        help="Maximum number of files allowed per project",
        default=10,
        scope=Scope.settings
    )

    max_file_size = Integer(
        display_name="Maximum File Size (bytes)",
        help="Maximum size per file in bytes",
        default=100000,
        scope=Scope.settings
    )

    allowed_file_extensions = ListField(
        display_name="Allowed File Extensions",
        help="List of allowed file extensions",
        default=[".py", ".java", ".cpp", ".c", ".js", ".h", ".hpp", ".txt", ".md"],
        scope=Scope.settings
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
        help="Student's best score for this problem",
        default=0.0,
        scope=Scope.user_state
    )

    submission_count = Integer(
        display_name="Submission Count",
        help="Number of submissions made by the student",
        default=0,
        scope=Scope.user_state
    )

    # Studio editable fields
    editable_fields = [
        'display_name',
        'problem_statement',
        'supported_languages',
        'default_language',
        'judge0_api_url',
        'judge0_api_key',
        'judge0_api_host',
        'test_cases',
        'max_score',
        'execution_time_limit',
        'memory_limit',
        'max_files',
        'max_file_size',
        'allowed_file_extensions'
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._initialize_student_files()

    def _initialize_student_files(self):
        """Initialize student files if none exist"""
        if not self.student_files:
            default_lang = self.default_language or 'python'
            lang_config = self.supported_languages.get(default_lang, {})
            template = lang_config.get('template', '# Write your code here')
            extension = lang_config.get('extension', 'py')
            
            self.student_files = {
                f'main.{extension}': {
                    'content': template,
                    'language': default_lang,
                    'created': datetime.now(timezone.utc).isoformat(),
                    'modified': datetime.now(timezone.utc).isoformat()
                }
            }
            self.active_file = f'main.{extension}'
            self.current_language = default_lang

    def student_view(self, context=None):
        """Render the student view of the XBlock"""
        context = context or {}
        
        # Ensure student files are initialized
        self._initialize_student_files()
        
        # Prepare context for template
        template_context = {
            'xblock': self,
            'problem_statement': self.problem_statement,
            'test_cases': self.test_cases,
            'student_files': self.student_files,
            'current_language': self.current_language,
            'active_file': self.active_file,
            'supported_languages': self.supported_languages,
            'current_score': self.current_score,
            'best_score': self.best_score,
            'max_score': self.max_score,
            'submission_count': self.submission_count,
        }
        
        # Render the template
        html = loader.render_template('advanced_coding/advanced_coding.html', template_context)
        
        # Create fragment
        fragment = Fragment(html)
        
        # Add CSS
        fragment.add_css(loader.load_unicode('static/css/advanced_coding.css'))
        
        # Add JavaScript
        fragment.add_javascript(loader.load_unicode('static/js/advanced_coding.js'))
        
        # Add initialization data
        fragment.initialize_js('AdvancedCodingXBlock', {
            'xblock_id': str(self.scope_ids.usage_id),
            'student_files': self.student_files,
            'supported_languages': self.supported_languages,
            'current_language': self.current_language,
            'active_file': self.active_file,
            'test_cases': self.test_cases,
            'max_score': self.max_score,
            'current_score': self.current_score,
            'best_score': self.best_score,
            'submission_count': self.submission_count,
        })
        
        return fragment

    def studio_view(self, context=None):
        """Render the studio view of the XBlock"""
        return self._editable_view(context)

    def _editable_view(self, context=None):
        """Render the editable view for studio"""
        context = context or {}
        context.update({
            'xblock': self,
            'editable_fields': self.editable_fields,
        })
        
        html = loader.render_template('static/html/advanced_coding_studio.html', context)
        fragment = Fragment(html)
        
        # Add studio-specific CSS and JS
        fragment.add_css(loader.load_unicode('static/css/advanced_coding_studio.css'))
        fragment.add_javascript(loader.load_unicode('static/js/advanced_coding_studio.js'))
        
        fragment.initialize_js('AdvancedCodingStudioXBlock', {
            'xblock_id': str(self.scope_ids.usage_id),
            'editable_fields': self.editable_fields,
        })
        
        return fragment

    @XBlock.json_handler
    def save_file(self, data, suffix=''):
        """Save a file with the given content"""
        try:
            filename = data.get('filename', '').strip()
            content = data.get('content', '')
            language = data.get('language', self.current_language)
            
            # Validate filename
            valid, msg = self.validate_file_name(filename)
            if not valid:
                return {'success': False, 'error': msg}
            
            # Validate content
            valid, msg = self.validate_file_content(content)
            if not valid:
                return {'success': False, 'error': msg}
            
            # Check file count limit
            if filename not in self.student_files and len(self.student_files) >= self.max_files:
                return {'success': False, 'error': f'Maximum file limit ({self.max_files}) reached'}
            
            # Save file
            self.student_files[filename] = {
                'content': content,
                'language': language,
                'created': datetime.now(timezone.utc).isoformat(),
                'modified': datetime.now(timezone.utc).isoformat()
            }
            
            # Update active file if this is a new file
            if filename not in self.student_files:
                self.active_file = filename
                self.current_language = language
            
            return {'success': True, 'filename': filename}
            
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            return {'success': False, 'error': 'Internal server error'}

    @XBlock.json_handler
    def delete_file(self, data, suffix=''):
        """Delete a file"""
        try:
            filename = data.get('filename', '').strip()
            
            if not filename:
                return {'success': False, 'error': 'Filename is required'}
            
            if filename not in self.student_files:
                return {'success': False, 'error': 'File not found'}
            
            # Don't allow deleting the last file
            if len(self.student_files) <= 1:
                return {'success': False, 'error': 'Cannot delete the last file'}
            
            # Remove file
            del self.student_files[filename]
            
            # Update active file if needed
            if self.active_file == filename:
                self.active_file = list(self.student_files.keys())[0]
                self.current_language = self.student_files[self.active_file]['language']
            
            return {'success': True, 'filename': filename}
            
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            return {'success': False, 'error': 'Internal server error'}

    @XBlock.json_handler
    def rename_file(self, data, suffix=''):
        """Rename a file"""
        try:
            old_filename = data.get('old_filename', '').strip()
            new_filename = data.get('new_filename', '').strip()
            
            if not old_filename or not new_filename:
                return {'success': False, 'error': 'Both old and new filenames are required'}
            
            if old_filename not in self.student_files:
                return {'success': False, 'error': 'File not found'}
            
            # Validate new filename
            valid, msg = self.validate_file_name(new_filename)
            if not valid:
                return {'success': False, 'error': msg}
            
            # Check if new filename already exists
            if new_filename in self.student_files:
                return {'success': False, 'error': 'File with that name already exists'}
            
            # Rename file
            file_data = self.student_files[old_filename]
            self.student_files[new_filename] = file_data
            del self.student_files[old_filename]
            
            # Update active file if needed
            if self.active_file == old_filename:
                self.active_file = new_filename
            
            return {'success': True, 'old_filename': old_filename, 'new_filename': new_filename}
            
        except Exception as e:
            logger.error(f"Error renaming file: {e}")
            return {'success': False, 'error': 'Internal server error'}

    @XBlock.json_handler
    def run_code(self, data, suffix=''):
        """Run code with Judge0 API"""
        try:
            if not self.judge0_api_key:
                return {'success': False, 'error': 'Judge0 API key not configured'}
            
            # Get active file content
            active_file = self.student_files.get(self.active_file)
            if not active_file:
                return {'success': False, 'error': 'No active file found'}
            
            code = active_file['content']
            language = active_file['language']
            
            # Get language configuration
            lang_config = self.supported_languages.get(language)
            if not lang_config:
                return {'success': False, 'error': f'Unsupported language: {language}'}
            
            # Prepare submission data
            submission_data = {
                'source_code': code,
                'language_id': lang_config['id'],
                'stdin': data.get('input', ''),
                'cpu_time_limit': self.execution_time_limit,
                'memory_limit': self.memory_limit
            }
            
            # Submit to Judge0
            headers = {
                'X-RapidAPI-Key': self.judge0_api_key,
                'X-RapidAPI-Host': self.judge0_api_host,
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                f"{self.judge0_api_url}/submissions",
                json=submission_data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code != 201:
                return {'success': False, 'error': f'Judge0 API error: {response.status_code}'}
            
            submission = response.json()
            token = submission.get('token')
            
            # Wait for result
            time.sleep(2)  # Simple wait - in production, use polling
            
            # Get result
            result_response = requests.get(
                f"{self.judge0_api_url}/submissions/{token}",
                headers=headers,
                timeout=30
            )
            
            if result_response.status_code != 200:
                return {'success': False, 'error': 'Failed to get execution result'}
            
            result = result_response.json()
            
            return {
                'success': True,
                'output': result.get('stdout', ''),
                'error': result.get('stderr', ''),
                'status': result.get('status', {}).get('description', 'Unknown'),
                'execution_time': result.get('time', 0),
                'memory_used': result.get('memory', 0)
            }
            
        except Exception as e:
            logger.error(f"Error running code: {e}")
            return {'success': False, 'error': 'Internal server error'}

    @XBlock.json_handler
    def submit_solution(self, data, suffix=''):
        """Submit solution for grading"""
        try:
            # Run all test cases
            test_results = []
            total_score = 0
            
            for test_case in self.test_cases:
                # Run test case
                test_data = {
                    'input': test_case.get('input', ''),
                    'language': self.current_language
                }
                
                result = self.run_code(test_data)
                if not result['success']:
                    test_results.append({
                        'test_id': test_case['id'],
                        'passed': False,
                        'error': result['error'],
                        'points': 0
                    })
                    continue
                
                # Check output
                expected = test_case.get('expected_output', '').strip()
                actual = result.get('output', '').strip()
                passed = expected == actual
                
                points = test_case.get('points', 0) if passed else 0
                total_score += points
                
                test_results.append({
                    'test_id': test_case['id'],
                    'passed': passed,
                    'expected': expected,
                    'actual': actual,
                    'points': points,
                    'execution_time': result.get('execution_time', 0)
                })
            
            # Create submission record
            submission = {
                'id': str(uuid.uuid4()),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'test_results': test_results,
                'total_score': total_score,
                'files': dict(self.student_files)
            }
            
            self.submissions.append(submission)
            self.submission_count += 1
            self.current_score = total_score
            
            if total_score > self.best_score:
                self.best_score = total_score
            
            return {
                'success': True,
                'total_score': total_score,
                'max_score': self.max_score,
                'test_results': test_results,
                'submission_id': submission['id']
            }
            
        except Exception as e:
            logger.error(f"Error submitting solution: {e}")
            return {'success': False, 'error': 'Internal server error'}

    def validate_file_name(self, filename):
        """Validate a filename"""
        if not filename:
            return False, "Filename cannot be empty"
        
        if '.' not in filename:
            return False, "Filename must have an extension"
        
        name, ext = filename.rsplit('.', 1)
        if not name:
            return False, "Filename cannot start with a dot"
        
        if ext not in [ext.lstrip('.') for ext in self.allowed_file_extensions]:
            return False, f"File extension '.{ext}' is not allowed"
        
        # Check for invalid characters
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
        if any(char in filename for char in invalid_chars):
            return False, "Filename contains invalid characters"
        
        return True, ""

    def validate_file_content(self, content):
        """Validate file content"""
        if not isinstance(content, str):
            return False, "Content must be a string"
        
        if len(content) > self.max_file_size:
            return False, f"File content exceeds maximum size ({self.max_file_size} bytes)"
        
        # Basic security check - look for potentially dangerous patterns
        dangerous_patterns = [
            'import os', 'import sys', 'import subprocess',
            'eval(', 'exec(', '__import__(',
            'open(', 'file(', 'raw_input(',
            'input(', 'compile('
        ]
        
        content_lower = content.lower()
        for pattern in dangerous_patterns:
            if pattern in content_lower:
                return False, f"Content contains potentially dangerous pattern: {pattern}"
        
        return True, ""

    def workbench_scenarios(self):
        """Return workbench scenarios for testing"""
        return [
            ("Advanced Coding XBlock",
             """<advanced_coding/>
              """)
        ]
