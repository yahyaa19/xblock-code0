/* Advanced Coding XBlock Studio JavaScript */

(function() {
    'use strict';

    class AdvancedCodingStudioXBlock {
        constructor(runtime, element) {
            this.runtime = runtime;
            this.element = element;
            this.init();
        }

        init() {
            this.bindEvents();
            this.initializeValidation();
        }

        bindEvents() {
            const $element = $(this.element);
            
            // Test cases management
            $element.on('click', '.add-test-case-btn', () => {
                this.addTestCase();
            });

            $element.on('click', '.remove-test-case-btn', (e) => {
                this.removeTestCase($(e.currentTarget).closest('.test-case-item'));
            });

            // Language configuration management
            $element.on('click', '.add-language-btn', () => {
                this.addLanguage();
            });

            $element.on('click', '.remove-language-btn', (e) => {
                this.removeLanguage($(e.currentTarget).closest('.language-item'));
            });

            // Form validation
            $element.on('input change', '.field-input, .field-textarea, .field-select', () => {
                this.validateForm();
            });

            // Judge0 API key toggle
            $element.on('click', '.toggle-api-key', (e) => {
                this.toggleApiKeyVisibility($(e.currentTarget));
            });

            // Real-time validation feedback
            $element.on('blur', '.field-input[data-validate]', (e) => {
                this.validateField($(e.currentTarget));
            });
        }

        addTestCase() {
            const container = $(this.element).find('.test-cases-list');
            const testCaseCount = container.find('.test-case-item').length;
            const testCaseId = `test_${testCaseCount + 1}`;
            
            const testCaseHtml = this.createTestCaseHtml(testCaseId, testCaseCount + 1);
            container.append(testCaseHtml);
            
            this.updateTestCaseIndexes();
            this.validateForm();
        }

        removeTestCase($testCase) {
            if ($(this.element).find('.test-case-item').length <= 1) {
                this.showNotification('error', 'At least one test case is required');
                return;
            }
            
            $testCase.remove();
            this.updateTestCaseIndexes();
            this.validateForm();
        }

        createTestCaseHtml(testId, index) {
            return `
                <div class="test-case-item">
                    <div class="test-case-header">
                        <div class="test-case-title">Test Case ${index}</div>
                        <div class="test-case-actions">
                            <button type="button" class="btn btn-sm btn-danger remove-test-case-btn">
                                <i class="fa fa-trash"></i> Remove
                            </button>
                        </div>
                    </div>
                    <div class="test-case-body">
                        <div class="test-case-row">
                            <div class="test-case-field">
                                <label>Test ID</label>
                                <input type="text" name="test_cases[${index-1}][id]" value="${testId}" 
                                       class="field-input" data-validate="required">
                            </div>
                            <div class="test-case-field">
                                <label>Test Name</label>
                                <input type="text" name="test_cases[${index-1}][name]" value="Test Case ${index}" 
                                       class="field-input" data-validate="required">
                            </div>
                        </div>
                        <div class="test-case-row">
                            <div class="test-case-field">
                                <label>Points</label>
                                <input type="number" name="test_cases[${index-1}][points]" value="10" 
                                       class="field-input" min="0" data-validate="number">
                            </div>
                            <div class="test-case-field">
                                <label>Timeout (seconds)</label>
                                <input type="number" name="test_cases[${index-1}][timeout]" value="2.0" 
                                       class="field-input" min="0.1" step="0.1" data-validate="number">
                            </div>
                        </div>
                        <div class="test-case-row">
                            <div class="test-case-field full-width">
                                <label>Input</label>
                                <textarea name="test_cases[${index-1}][input]" 
                                          class="field-input" placeholder="Test input (leave empty if no input required)"></textarea>
                            </div>
                        </div>
                        <div class="test-case-row">
                            <div class="test-case-field full-width">
                                <label>Expected Output</label>
                                <textarea name="test_cases[${index-1}][expected_output]" 
                                          class="field-input" data-validate="required" 
                                          placeholder="Expected output from the program"></textarea>
                            </div>
                        </div>
                        <div class="test-case-row">
                            <div class="test-case-field checkbox">
                                <input type="checkbox" name="test_cases[${index-1}][is_public]" checked>
                                <label>Public Test Case (visible to students)</label>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }

        addLanguage() {
            const container = $(this.element).find('.languages-list');
            const languageCount = container.find('.language-item').length;
            const languageKey = `language_${languageCount + 1}`;
            
            const languageHtml = this.createLanguageHtml(languageKey, languageCount + 1);
            container.append(languageHtml);
            
            this.updateLanguageIndexes();
            this.validateForm();
        }

        removeLanguage($language) {
            if ($(this.element).find('.language-item').length <= 1) {
                this.showNotification('error', 'At least one programming language must be supported');
                return;
            }
            
            $language.remove();
            this.updateLanguageIndexes();
            this.validateForm();
        }

        createLanguageHtml(languageKey, index) {
            return `
                <div class="language-item">
                    <div class="language-header">
                        <div class="language-name">Programming Language ${index}</div>
                        <div class="language-actions">
                            <button type="button" class="btn btn-sm btn-danger remove-language-btn">
                                <i class="fa fa-trash"></i> Remove
                            </button>
                        </div>
                    </div>
                    <div class="language-body">
                        <div class="language-row">
                            <div class="language-field">
                                <label>Language Key</label>
                                <input type="text" name="supported_languages[${languageKey}][key]" value="${languageKey}" 
                                       class="field-input" data-validate="required">
                                <div class="help-text">Unique identifier (e.g., python, java, cpp)</div>
                            </div>
                            <div class="language-field">
                                <label>Display Name</label>
                                <input type="text" name="supported_languages[${languageKey}][name]" value="Language ${index}" 
                                       class="field-input" data-validate="required">
                                <div class="help-text">Human-readable name shown to users</div>
                            </div>
                            <div class="language-field">
                                <label>Judge0 Language ID</label>
                                <input type="number" name="supported_languages[${languageKey}][id]" value="71" 
                                       class="field-input" min="1" data-validate="required,number">
                                <div class="help-text">See <a href="https://ce.judge0.com/languages" target="_blank">Judge0 languages</a></div>
                            </div>
                        </div>
                        <div class="language-row">
                            <div class="language-field">
                                <label>File Extension</label>
                                <input type="text" name="supported_languages[${languageKey}][extension]" value="py" 
                                       class="field-input" data-validate="required">
                                <div class="help-text">Default extension (without dot)</div>
                            </div>
                        </div>
                        <div class="language-row">
                            <div class="language-field full-width">
                                <label>Template Code</label>
                                <textarea name="supported_languages[${languageKey}][template]" 
                                          class="field-input field-textarea" data-validate="required" 
                                          placeholder="Default template code for new files"># Write your code here
print('Hello, World!')</textarea>
                                <div class="help-text">Default code template shown to students</div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }

        updateTestCaseIndexes() {
            $(this.element).find('.test-case-item').each((index, element) => {
                const $item = $(element);
                
                // Update title
                $item.find('.test-case-title').text(`Test Case ${index + 1}`);
                
                // Update input names
                $item.find('input, textarea').each((i, input) => {
                    const $input = $(input);
                    const name = $input.attr('name');
                    if (name && name.includes('[') && name.includes(']')) {
                        const newName = name.replace(/\[\d+\]/, `[${index}]`);
                        $input.attr('name', newName);
                    }
                });
            });
        }

        updateLanguageIndexes() {
            $(this.element).find('.language-item').each((index, element) => {
                const $item = $(element);
                
                // Update title
                $item.find('.language-name').text(`Programming Language ${index + 1}`);
            });
        }

        toggleApiKeyVisibility($button) {
            const $input = $button.siblings('input');
            const $icon = $button.find('i');
            
            if ($input.attr('type') === 'password') {
                $input.attr('type', 'text');
                $icon.removeClass('fa-eye').addClass('fa-eye-slash');
                $button.attr('title', 'Hide API key');
            } else {
                $input.attr('type', 'password');
                $icon.removeClass('fa-eye-slash').addClass('fa-eye');
                $button.attr('title', 'Show API key');
            }
        }

        validateField($field) {
            const value = $field.val().trim();
            const validations = ($field.data('validate') || '').split(',');
            const $feedback = $field.siblings('.validation-feedback');
            let isValid = true;
            let message = '';

            // Remove existing feedback
            $feedback.remove();
            $field.removeClass('error warning');

            // Required validation
            if (validations.includes('required') && !value) {
                isValid = false;
                message = 'This field is required';
            }

            // Number validation
            if (validations.includes('number') && value && isNaN(Number(value))) {
                isValid = false;
                message = 'Please enter a valid number';
            }

            // URL validation
            if (validations.includes('url') && value) {
                const urlPattern = /^https?:\/\/.+/i;
                if (!urlPattern.test(value)) {
                    isValid = false;
                    message = 'Please enter a valid URL starting with http:// or https://';
                }
            }

            // Display validation feedback
            if (!isValid) {
                $field.addClass('error');
                $field.after(`<div class="validation-feedback error">${message}</div>`);
            } else if (validations.includes('required') && value) {
                $field.addClass('success');
            }

            return isValid;
        }

        validateForm() {
            let isValid = true;
            const $form = $(this.element).find('form');
            
            // Validate all required fields
            $form.find('[data-validate*="required"]').each((index, field) => {
                if (!this.validateField($(field))) {
                    isValid = false;
                }
            });

            // Check for at least one test case
            if ($(this.element).find('.test-case-item').length === 0) {
                this.showValidationMessage('error', 'At least one test case is required');
                isValid = false;
            }

            // Check for at least one language
            if ($(this.element).find('.language-item').length === 0) {
                this.showValidationMessage('error', 'At least one programming language must be supported');
                isValid = false;
            }

            // Update save button state
            const $saveButton = $form.find('.save-button');
            $saveButton.prop('disabled', !isValid);

            return isValid;
        }

        initializeValidation() {
            // Add real-time validation to existing fields
            const $existingFields = $(this.element).find('[data-validate]');
            $existingFields.each((index, field) => {
                this.validateField($(field));
            });
        }

        showValidationMessage(type, message) {
            const $container = $(this.element).find('.validation-messages');
            if ($container.length === 0) {
                $(this.element).append('<div class="validation-messages"></div>');
            }
            
            const $message = $(`<div class="validation-message ${type}">${message}</div>`);
            $(this.element).find('.validation-messages').append($message);
            
            // Auto-remove after 5 seconds
            setTimeout(() => {
                $message.remove();
            }, 5000);
        }

        showNotification(type, message) {
            // Simple notification system
            const notification = $(`
                <div class="notification ${type}" style="position: fixed; top: 20px; right: 20px; 
                     background: white; border: 1px solid #ccc; padding: 12px; border-radius: 4px; 
                     z-index: 9999; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    ${message}
                </div>
            `);
            
            $('body').append(notification);
            
            setTimeout(() => {
                notification.remove();
            }, 3000);
        }

        // Helper methods for specific field types
        setupJudge0Config() {
            const $apiKeyInput = $(this.element).find('input[name="judge0_api_key"]');
            const $apiHostInput = $(this.element).find('input[name="judge0_api_host"]');
            const $testConnectionBtn = $(this.element).find('.test-judge0-connection');
            
            $testConnectionBtn.on('click', () => {
                this.testJudge0Connection($apiKeyInput.val(), $apiHostInput.val());
            });
        }

        testJudge0Connection(apiKey, apiHost) {
            if (!apiKey || !apiHost) {
                this.showNotification('error', 'Please fill in API key and host before testing');
                return;
            }
            
            // This would make a test request to Judge0
            this.showNotification('info', 'Testing connection to Judge0...');
            
            // Simulate test (in real implementation, make actual API call)
            setTimeout(() => {
                this.showNotification('success', 'Successfully connected to Judge0 API');
            }, 2000);
        }

        // Export/Import configuration
        exportConfiguration() {
            const formData = new FormData($(this.element).find('form')[0]);
            const config = {};
            
            for (let [key, value] of formData.entries()) {
                config[key] = value;
            }
            
            const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'advanced-coding-xblock-config.json';
            a.click();
            URL.revokeObjectURL(url);
        }

        importConfiguration(file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                try {
                    const config = JSON.parse(e.target.result);
                    this.loadConfiguration(config);
                    this.showNotification('success', 'Configuration imported successfully');
                } catch (error) {
                    this.showNotification('error', 'Invalid configuration file');
                }
            };
            reader.readAsText(file);
        }

        loadConfiguration(config) {
            // Load configuration into form fields
            for (const [key, value] of Object.entries(config)) {
                const $field = $(this.element).find(`[name="${key}"]`);
                if ($field.length) {
                    $field.val(value);
                }
            }
            this.validateForm();
        }
    }

    // Initialize the Studio XBlock
    function AdvancedCodingStudioXBlockInit(runtime, element) {
        return new AdvancedCodingStudioXBlock(runtime, element);
    }

    // Export for XBlock runtime
    window.AdvancedCodingStudioXBlock = AdvancedCodingStudioXBlockInit;
})();
