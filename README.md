# Advanced Coding XBlock

A comprehensive coding assessment platform for Open edX that provides advanced coding capabilities with Monaco Editor and Judge0 API integration.

## Features

### 🚀 Core Features
- **Monaco Editor Integration**: Professional code editor with syntax highlighting, autocomplete, and error detection
- **Multi-File Support**: Create, edit, rename, and delete files within projects
- **Judge0 API Integration**: Secure code execution with support for multiple programming languages
- **Automated Testing**: Public and hidden test cases with detailed feedback
- **Real-time Grading**: Automatic scoring based on test case results
- **Multi-Language Support**: Python, Java, C++, C, JavaScript, and more

### 👨‍💻 Developer Experience
- **Intuitive Interface**: Tabbed file management with drag-and-drop functionality
- **Keyboard Shortcuts**: Ctrl+S (save), Ctrl+R (run), Ctrl+Enter (submit)
- **Auto-save**: Automatic file saving every 30 seconds and after 2 seconds of inactivity
- **Custom Input Testing**: Test code with custom input before submission
- **Responsive Design**: Works on desktop, tablet, and mobile devices

### 🏫 Instructor Tools
- **Flexible Configuration**: Easy setup through Open edX Studio
- **Test Case Management**: Add, edit, and remove test cases with drag-and-drop
- **Language Configuration**: Configure supported languages and templates
- **Security Settings**: File size limits, execution timeouts, and content filtering
- **Analytics**: Track student submissions and performance

### 🔒 Security Features
- **Input Validation**: Comprehensive validation of file names, content, and user input
- **Sandboxed Execution**: All code runs in isolated Judge0 containers
- **Content Filtering**: Detection and blocking of potentially dangerous code patterns
- **Resource Limits**: Configurable CPU time, memory, and execution limits

## Installation

### Prerequisites
- Open edX installation (Lilac or newer recommended)
- Python 3.8+
- Node.js (for Monaco Editor CDN fallback)
- Judge0 API access (RapidAPI or self-hosted)

### Step 1: Install the XBlock

```bash
# Install from source
git clone https://github.com/yourusername/advanced-coding-xblock.git
cd advanced-coding-xblock
pip install -e .

# Or install from PyPI (when published)
pip install advanced-coding-xblock
```

### Step 2: Enable in Open edX

Add the XBlock to your Open edX configuration:

```python
# In /edx/app/edxapp/cms.env.json and lms.env.json
XBLOCK_SETTINGS = {
    "AdvancedCodingXBlock": {
        "judges": {
            "judge0": {
                "api_url": "https://judge0-ce.p.rapidapi.com",
                "api_key": "your-rapidapi-key",
                "api_host": "judge0-ce.p.rapidapi.com"
            }
        }
    }
}

# Add to ADVANCED_COMPONENT_TYPES
ADVANCED_COMPONENT_TYPES = [
    {
        "component": "advanced_coding",
        "boilerplate_name": None,
        "tab": "advanced",
        "editor_saved_state": "never"
    }
]
```

### Step 3: Configure Judge0 API

1. Sign up for RapidAPI: https://rapidapi.com/
2. Subscribe to Judge0 CE: https://rapidapi.com/judge0-official/api/judge0-ce/
3. Get your API key and configure it in the XBlock settings

### Step 4: Restart Open edX Services

```bash
sudo /edx/bin/supervisorctl restart edxapp:*
```

## Configuration

### Judge0 Setup

The XBlock requires Judge0 API for code execution. You can use either:

1. **RapidAPI (Recommended for development)**:
   - Easy setup with free tier
   - Managed service with high availability
   - Built-in rate limiting and monitoring

2. **Self-hosted Judge0**:
   - More control and customization
   - Better for production with high volume
   - Requires Docker and server management

### Language Configuration

Configure supported programming languages in Studio:

```json
{
  "python": {
    "id": 71,
    "name": "Python 3",
    "extension": "py",
    "template": "# Write your Python code here\nprint('Hello, World!')"
  },
  "java": {
    "id": 62,
    "name": "Java",
    "extension": "java",
    "template": "public class Main {\n    public static void main(String[] args) {\n        System.out.println(\"Hello, World!\");\n    }\n}"
  }
}
```

### Test Cases Configuration

Set up automated test cases for grading:

```json
[
  {
    "id": "test_1",
    "name": "Basic Test",
    "input": "5 3",
    "expected_output": "8",
    "is_public": true,
    "points": 10,
    "timeout": 2.0
  }
]
```

## Usage

### For Instructors

1. **Add XBlock to Course**:
   - Go to Studio → Advanced Components
   - Select "Advanced Coding Assessment"
   - Configure problem statement and settings

2. **Configure Problem**:
   - Set problem statement in Markdown
   - Add test cases with input/output pairs
   - Configure supported languages
   - Set grading parameters

3. **Monitor Student Progress**:
   - View submission history
   - Track performance analytics
   - Reset student data if needed

### For Students

1. **Write Code**:
   - Use the integrated Monaco Editor
   - Create multiple files as needed
   - Switch between programming languages

2. **Test Code**:
   - Run code with custom input
   - See real-time output and errors
   - Debug before submission

3. **Submit for Grading**:
   - Run automated test cases
   - Get immediate feedback
   - See detailed test results

## API Reference

### XBlock Handlers

- `save_file`: Save or update a file
- `delete_file`: Delete a file from the project
- `rename_file`: Rename an existing file
- `run_code`: Execute code with optional input
- `submit_solution`: Submit solution for automated grading
- `get_student_data`: Retrieve current student state

### Configuration Fields

- `display_name`: Display name for the component
- `problem_statement`: Problem description in Markdown
- `supported_languages`: Dictionary of supported languages
- `test_cases`: List of test cases for grading
- `max_score`: Maximum possible score
- `execution_time_limit`: Code execution timeout
- `memory_limit`: Memory limit for execution
- `judge0_api_*`: Judge0 API configuration

## Development

### Setting up Development Environment

```bash
# Clone repository
git clone https://github.com/yourusername/advanced-coding-xblock.git
cd advanced-coding-xblock

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Run linting
flake8 advanced_coding/
pylint advanced_coding/
```

### Testing

```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Coverage report
pytest --cov=advanced_coding --cov-report=html
```

### Building for Production

```bash
# Build package
python setup.py sdist bdist_wheel

# Upload to PyPI (maintainers only)
twine upload dist/*
```

## Security Considerations

### Code Execution Security

- All code execution happens in Judge0 sandboxed containers
- Strict resource limits prevent resource exhaustion
- Input validation prevents injection attacks
- Content filtering blocks dangerous patterns

### Data Protection

- Student code is stored securely in Open edX database
- API keys are encrypted in configuration
- No student data is sent to external services except for execution
- GDPR and FERPA compliant data handling

### Best Practices

1. **Use HTTPS**: Always use HTTPS for Judge0 API calls
2. **Rotate API Keys**: Regular rotation of Judge0 API keys
3. **Monitor Usage**: Track API usage and set appropriate limits
4. **Content Review**: Review and approve problem statements
5. **Regular Updates**: Keep XBlock and dependencies updated

## Troubleshooting

### Common Issues

**Monaco Editor Not Loading**:
- Check browser console for CDN errors
- Verify internet connectivity for CDN access
- Try clearing browser cache

**Judge0 API Errors**:
- Verify API key and host configuration
- Check RapidAPI subscription status
- Review rate limiting and quotas

**Code Execution Timeouts**:
- Increase execution time limits
- Optimize test case complexity
- Check Judge0 service status

**File Save Failures**:
- Check file size limits
- Verify file name restrictions
- Review content validation rules

### Getting Help

1. **Documentation**: Check this README and inline documentation
2. **Issues**: Report bugs on GitHub Issues
3. **Discussions**: Join community discussions
4. **Support**: Contact maintainers for enterprise support

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

### Code Standards

- Follow PEP 8 for Python code
- Use ESLint for JavaScript
- Write comprehensive tests
- Document all public APIs

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **Monaco Editor**: Microsoft's excellent code editor
- **Judge0**: Robust code execution platform
- **Open edX**: Open source learning platform
- **Contributors**: All the amazing contributors to this project

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and updates.

---

For more information, visit our [documentation site](https://your-docs-site.com) or join our [community forum](https://your-community.com).
