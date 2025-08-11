/* Advanced Coding XBlock JavaScript Implementation */

(function() {
    'use strict';

    // Language mappings for Monaco Editor
    const LANGUAGE_MAPPINGS = {
        'python': 'python',
        'java': 'java',
        'cpp': 'cpp',
        'c': 'c',
        'javascript': 'javascript',
        'typescript': 'typescript',
        'html': 'html',
        'css': 'css',
        'json': 'json',
        'xml': 'xml',
        'markdown': 'markdown'
    };

    class AdvancedCodingXBlock {
        constructor(runtime, element, initArgs) {
            this.runtime = runtime;
            this.element = element;
            this.initArgs = initArgs || {};
            
            // Parse initialization data
            this.xblockId = this.initArgs.xblock_id;
            this.studentFiles = this.initArgs.student_files || {};
            this.supportedLanguages = this.initArgs.supported_languages || {};
            this.currentLanguage = this.initArgs.current_language || 'python';
            this.activeFile = this.initArgs.active_file || 'main.py';
            
            // Monaco Editor instance
            this.editor = null;
            this.monacoLoaded = false;
            
            // UI state
            this.isExecuting = false;
            this.currentModal = null;
            
            // Initialize the XBlock
            this.init();
        }

        init() {
            this.bindEvents();
            this.initializeMonacoEditor();
            this.updateUI();
            this.loadActiveFile();
        }

        bindEvents() {
            const $element = $(this.element);
            
            // File tab events
            $element.on('click', '.file-tab', (e) => {
                const filename = $(e.currentTarget).data('filename');
                const language = $(e.currentTarget).data('language');
                this.switchToFile(filename, language);
            });

            $element.on('click', '.tab-close', (e) => {
                e.stopPropagation();
                const filename = $(e.currentTarget).data('filename');
                this.deleteFile(filename);
            });

            // File management events
            $element.on('click', '.new-file-btn', () => {
                this.showNewFileModal();
            });

            $element.on('click', '.rename-file-btn', () => {
                this.showRenameFileModal();
            });

            $element.on('click', '.delete-file-btn', () => {
                this.deleteFile(this.activeFile);
            });

            // Language selector
            $element.on('change', `#language-select-${this.xblockId}`, (e) => {
                this.changeLanguage($(e.target).val());
            });

            // Code execution events
            $element.on('click', '.run-code-btn', () => {
                this.runCode();
            });

            $element.on('click', '.run-with-input-btn', () => {
                this.runCodeWithInput();
            });

            $element.on('click', '.submit-solution-btn', () => {
                this.submitSolution();
            });

            $element.on('click', '.save-file-btn', () => {
                this.saveCurrentFile();
            });

            // Output tab events
            $element.on('click', '.output-tab', (e) => {
                this.switchOutputTab($(e.target).data('tab'));
            });

            $element.on('click', '.clear-console-btn', () => {
                this.clearConsole();
            });

            // Modal events
            $element.on('click', '.modal-close, .modal-cancel', () => {
                this.hideModal();
            });

            $element.on('click', '.modal-confirm', () => {
                this.handleModalConfirm();
            });

            // Keyboard shortcuts
            $element.on('keydown', (e) => {
                this.handleKeyboardShortcuts(e);
            });

            // Auto-save functionality
            if (this.editor) {
                this.setupAutoSave();
            }
        }

        async initializeMonacoEditor() {
            try {
                // Load Monaco Editor if not already loaded
                if (typeof monaco === 'undefined') {
                    await this.loadMonacoEditor();
                }

                // Create editor instance
                const editorContainer = document.getElementById(`monaco-editor-${this.xblockId}`);
                if (!editorContainer) {
                    console.error('Monaco Editor container not found');
                    return;
                }

                // Get current file content
                const fileData = this.studentFiles[this.activeFile] || {};
                const content = fileData.content || this.getTemplateForLanguage(this.currentLanguage);
                const language = this.getMonacoLanguage(this.currentLanguage);

                // Editor configuration
                this.editor = monaco.editor.create(editorContainer, {
                    value: content,
                    language: language,
                    theme: 'vs-dark',
                    automaticLayout: true,
                    fontSize: 14,
                    lineNumbers: 'on',
                    minimap: {
                        enabled: true
                    },
                    scrollBeyondLastLine: false,
                    wordWrap: 'on',
                    folding: true,
                    renderLineHighlight: 'line',
                    selectOnLineNumbers: true,
                    roundedSelection: false,
                    readOnly: false,
                    cursorStyle: 'line',
                    automaticLayout: true,
                    glyphMargin: true,
                    useTabStops: false,
                    selectionHighlight: false,
                    lineHeight: 19,
                    renderWhitespace: 'boundary',
                    contextmenu: true,
                    mouseWheelZoom: true,
                    multiCursorModifier: 'ctrlCmd',
                    accessibilitySupport: 'auto'
                });

                // Editor event handlers
                this.editor.onDidChangeModelContent(() => {
                    this.onEditorContentChange();
                });

                this.editor.onDidChangeCursorPosition(() => {
                    this.updateStatusBar();
                });

                this.monacoLoaded = true;
                this.setupAutoSave();

            } catch (error) {
                console.error('Failed to initialize Monaco Editor:', error);
                this.showFallbackEditor();
            }
        }

        async loadMonacoEditor() {
            return new Promise((resolve, reject) => {
                if (typeof monaco !== 'undefined') {
                    resolve();
                    return;
                }

                // Load Monaco Editor from CDN
                const script = document.createElement('script');
                script.src = 'https://cdn.jsdelivr.net/npm/monaco-editor@0.44.0/min/vs/loader.js';
                script.onload = () => {
                    require.config({ paths: { 'vs': 'https://cdn.jsdelivr.net/npm/monaco-editor@0.44.0/min/vs' }});
                    require(['vs/editor/editor.main'], () => {
                        resolve();
                    });
                };
                script.onerror = reject;
                document.head.appendChild(script);
            });
        }

        showFallbackEditor() {
            // Show a basic textarea fallback if Monaco fails to load
            const container = document.getElementById(`monaco-editor-${this.xblockId}`);
            const fileData = this.studentFiles[this.activeFile] || {};
            const content = fileData.content || '';

            container.innerHTML = `
                <textarea class="fallback-editor" style="width: 100%; height: 100%; 
                         font-family: monospace; font-size: 14px; border: none; 
                         resize: none; outline: none; padding: 10px;">${content}</textarea>
            `;

            const textarea = container.querySelector('.fallback-editor');
            textarea.addEventListener('input', () => {
                this.onEditorContentChange();
            });
        }

        getMonacoLanguage(language) {
            return LANGUAGE_MAPPINGS[language] || 'plaintext';
        }

        getTemplateForLanguage(language) {
            const langConfig = this.supportedLanguages[language];
            return langConfig ? langConfig.template : '// Write your code here';
        }

        switchToFile(filename, language) {
            if (this.activeFile === filename) return;

            // Save current file before switching
            this.saveCurrentFile();

            // Update active file
            this.activeFile = filename;
            this.currentLanguage = language;

            // Update editor content and language
            this.loadActiveFile();
            this.updateFileTabsUI();
            this.updateLanguageSelector();
        }

        loadActiveFile() {
            const fileData = this.studentFiles[this.activeFile] || {};
            const content = fileData.content || this.getTemplateForLanguage(this.currentLanguage);

            if (this.editor) {
                const model = this.editor.getModel();
                const language = this.getMonacoLanguage(this.currentLanguage);
                
                // Update model content
                model.setValue(content);
                
                // Update language
                monaco.editor.setModelLanguage(model, language);
            } else if (this.element.querySelector('.fallback-editor')) {
                this.element.querySelector('.fallback-editor').value = content;
            }

            this.updateStatusBar();
        }

        onEditorContentChange() {
            // Mark file as modified
            this.markFileAsModified(this.activeFile);
            
            // Trigger auto-save after delay
            if (this.autoSaveTimeout) {
                clearTimeout(this.autoSaveTimeout);
            }
            this.autoSaveTimeout = setTimeout(() => {
                this.saveCurrentFile();
            }, 2000); // Auto-save after 2 seconds of inactivity
        }

        markFileAsModified(filename) {
            const tab = this.element.querySelector(`[data-filename="${filename}"]`);
            if (tab && !tab.classList.contains('modified')) {
                tab.classList.add('modified');
                const tabName = tab.querySelector('.tab-name');
                if (tabName && !tabName.textContent.includes('*')) {
                    tabName.textContent += '*';
                }
            }
        }

        removeModifiedMark(filename) {
            const tab = this.element.querySelector(`[data-filename="${filename}"]`);
            if (tab && tab.classList.contains('modified')) {
                tab.classList.remove('modified');
                const tabName = tab.querySelector('.tab-name');
                if (tabName && tabName.textContent.includes('*')) {
                    tabName.textContent = tabName.textContent.replace('*', '');
                }
            }
        }

        setupAutoSave() {
            // Auto-save every 30 seconds
            if (this.autoSaveInterval) {
                clearInterval(this.autoSaveInterval);
            }
            this.autoSaveInterval = setInterval(() => {
                this.saveCurrentFile();
            }, 30000);
        }

        saveCurrentFile() {
            const content = this.getCurrentEditorContent();
            const data = {
                filename: this.activeFile,
                content: content,
                language: this.currentLanguage
            };

            this.callHandler('save_file', data)
                .then(response => {
                    if (response.success) {
                        this.removeModifiedMark(this.activeFile);
                        this.updateStudentFiles(this.activeFile, content);
                    } else {
                        this.showNotification('error', response.error || 'Failed to save file');
                    }
                })
                .catch(error => {
                    console.error('Save failed:', error);
                    this.showNotification('error', 'Failed to save file');
                });
        }

        getCurrentEditorContent() {
            if (this.editor) {
                return this.editor.getValue();
            } else if (this.element.querySelector('.fallback-editor')) {
                return this.element.querySelector('.fallback-editor').value;
            }
            return '';
        }

        updateStudentFiles(filename, content) {
            if (!this.studentFiles[filename]) {
                this.studentFiles[filename] = {};
            }
            this.studentFiles[filename].content = content;
            this.studentFiles[filename].language = this.currentLanguage;
            this.studentFiles[filename].modified_at = new Date().toISOString();
        }

        showNewFileModal() {
            const modal = this.element.querySelector(`#file-modal-${this.xblockId}`);
            const title = modal.querySelector(`#modal-title-${this.xblockId}`);
            const filenameInput = modal.querySelector(`#filename-input-${this.xblockId}`);
            const languageSelect = modal.querySelector(`#modal-language-select-${this.xblockId}`);

            title.textContent = 'Create New File';
            filenameInput.value = '';
            languageSelect.value = this.currentLanguage;

            this.currentModal = 'new-file';
            this.showModal(modal);
        }

        showRenameFileModal() {
            const modal = this.element.querySelector(`#file-modal-${this.xblockId}`);
            const title = modal.querySelector(`#modal-title-${this.xblockId}`);
            const filenameInput = modal.querySelector(`#filename-input-${this.xblockId}`);
            const languageSelect = modal.querySelector(`#modal-language-select-${this.xblockId}`);

            title.textContent = 'Rename File';
            filenameInput.value = this.activeFile;
            languageSelect.value = this.currentLanguage;
            languageSelect.disabled = true;

            this.currentModal = 'rename-file';
            this.showModal(modal);
        }

        showModal(modal) {
            modal.style.display = 'flex';
            const filenameInput = modal.querySelector(`#filename-input-${this.xblockId}`);
            setTimeout(() => filenameInput.focus(), 100);
        }

        hideModal() {
            const modal = this.element.querySelector(`#file-modal-${this.xblockId}`);
            modal.style.display = 'none';
            const languageSelect = modal.querySelector(`#modal-language-select-${this.xblockId}`);
            languageSelect.disabled = false;
            this.currentModal = null;
        }

        handleModalConfirm() {
            if (this.currentModal === 'new-file') {
                this.createNewFile();
            } else if (this.currentModal === 'rename-file') {
                this.renameCurrentFile();
            }
        }

        createNewFile() {
            const filenameInput = this.element.querySelector(`#filename-input-${this.xblockId}`);
            const languageSelect = this.element.querySelector(`#modal-language-select-${this.xblockId}`);
            
            const filename = filenameInput.value.trim();
            const language = languageSelect.value;

            if (!filename) {
                this.showNotification('error', 'File name is required');
                return;
            }

            if (this.studentFiles[filename]) {
                this.showNotification('error', 'File already exists');
                return;
            }

            const content = this.getTemplateForLanguage(language);
            const data = {
                filename: filename,
                content: content,
                language: language
            };

            this.callHandler('save_file', data)
                .then(response => {
                    if (response.success) {
                        this.studentFiles[filename] = {
                            content: content,
                            language: language,
                            created_at: new Date().toISOString(),
                            modified_at: new Date().toISOString()
                        };
                        this.addFileTab(filename, language);
                        this.switchToFile(filename, language);
                        this.hideModal();
                        this.showNotification('success', `File '${filename}' created successfully`);
                    } else {
                        this.showNotification('error', response.error || 'Failed to create file');
                    }
                })
                .catch(error => {
                    console.error('Create file failed:', error);
                    this.showNotification('error', 'Failed to create file');
                });
        }

        renameCurrentFile() {
            const filenameInput = this.element.querySelector(`#filename-input-${this.xblockId}`);
            const newFilename = filenameInput.value.trim();

            if (!newFilename) {
                this.showNotification('error', 'File name is required');
                return;
            }

            if (newFilename === this.activeFile) {
                this.hideModal();
                return;
            }

            if (this.studentFiles[newFilename]) {
                this.showNotification('error', 'File with that name already exists');
                return;
            }

            const data = {
                old_filename: this.activeFile,
                new_filename: newFilename
            };

            this.callHandler('rename_file', data)
                .then(response => {
                    if (response.success) {
                        // Update local data
                        this.studentFiles[newFilename] = this.studentFiles[this.activeFile];
                        delete this.studentFiles[this.activeFile];
                        
                        // Update UI
                        this.updateFileTab(this.activeFile, newFilename);
                        this.activeFile = newFilename;
                        
                        this.hideModal();
                        this.showNotification('success', response.message);
                    } else {
                        this.showNotification('error', response.error || 'Failed to rename file');
                    }
                })
                .catch(error => {
                    console.error('Rename file failed:', error);
                    this.showNotification('error', 'Failed to rename file');
                });
        }

        deleteFile(filename) {
            if (Object.keys(this.studentFiles).length <= 1) {
                this.showNotification('error', 'Cannot delete the last file');
                return;
            }

            if (!confirm(`Are you sure you want to delete '${filename}'?`)) {
                return;
            }

            const data = { filename: filename };

            this.callHandler('delete_file', data)
                .then(response => {
                    if (response.success) {
                        // Remove from local data
                        delete this.studentFiles[filename];
                        
                        // Remove tab
                        this.removeFileTab(filename);
                        
                        // Switch to another file if this was active
                        if (this.activeFile === filename) {
                            const remainingFiles = Object.keys(this.studentFiles);
                            if (remainingFiles.length > 0) {
                                const firstFile = remainingFiles[0];
                                const firstFileData = this.studentFiles[firstFile];
                                this.switchToFile(firstFile, firstFileData.language);
                            }
                        }
                        
                        this.showNotification('success', response.message);
                    } else {
                        this.showNotification('error', response.error || 'Failed to delete file');
                    }
                })
                .catch(error => {
                    console.error('Delete file failed:', error);
                    this.showNotification('error', 'Failed to delete file');
                });
        }

        changeLanguage(newLanguage) {
            if (this.currentLanguage === newLanguage) return;

            this.currentLanguage = newLanguage;
            
            // Update editor language
            if (this.editor) {
                const model = this.editor.getModel();
                const monacoLanguage = this.getMonacoLanguage(newLanguage);
                monaco.editor.setModelLanguage(model, monacoLanguage);
            }

            // Update current file's language
            if (this.studentFiles[this.activeFile]) {
                this.studentFiles[this.activeFile].language = newLanguage;
            }

            // Update tab display
            const tab = this.element.querySelector(`[data-filename="${this.activeFile}"]`);
            if (tab) {
                tab.setAttribute('data-language', newLanguage);
            }

            // Save the change
            this.saveCurrentFile();
        }

        runCode() {
            if (this.isExecuting) return;

            this.setExecutionState(true);
            this.switchOutputTab('console');

            const data = {
                filename: this.activeFile,
                input: ''
            };

            this.callHandler('run_code', data)
                .then(response => {
                    this.displayExecutionResult(response);
                })
                .catch(error => {
                    console.error('Run code failed:', error);
                    this.displayExecutionError('Failed to execute code');
                })
                .finally(() => {
                    this.setExecutionState(false);
                });
        }

        runCodeWithInput() {
            if (this.isExecuting) return;

            const customInput = this.element.querySelector(`#custom-input-${this.xblockId}`).value;
            
            this.setExecutionState(true);
            this.switchOutputTab('console');

            const data = {
                filename: this.activeFile,
                input: customInput
            };

            this.callHandler('run_code', data)
                .then(response => {
                    this.displayExecutionResult(response);
                })
                .catch(error => {
                    console.error('Run code with input failed:', error);
                    this.displayExecutionError('Failed to execute code');
                })
                .finally(() => {
                    this.setExecutionState(false);
                });
        }

        submitSolution() {
            if (this.isExecuting) return;

            if (!confirm('Submit your solution for grading?')) return;

            this.setExecutionState(true);
            this.switchOutputTab('test-results');

            const data = {
                main_file: this.activeFile
            };

            this.callHandler('submit_solution', data)
                .then(response => {
                    if (response.success) {
                        this.displaySubmissionResult(response);
                        this.updateScoreDisplay(response.score, response.max_score);
                        this.showNotification('success', response.message);
                    } else {
                        this.showNotification('error', response.error || 'Submission failed');
                    }
                })
                .catch(error => {
                    console.error('Submit solution failed:', error);
                    this.showNotification('error', 'Failed to submit solution');
                })
                .finally(() => {
                    this.setExecutionState(false);
                });
        }

        displayExecutionResult(response) {
            const consoleOutput = this.element.querySelector(`#console-output-${this.xblockId}`);
            
            if (response.success) {
                let output = '';
                
                if (response.compile_output) {
                    output += `<div class="console-section">
                        <div class="console-label">Compilation:</div>
                        <div class="output-line">${this.escapeHtml(response.compile_output)}</div>
                    </div>`;
                }
                
                if (response.output) {
                    output += `<div class="console-section">
                        <div class="console-label">Output:</div>
                        <div class="success-line">${this.escapeHtml(response.output)}</div>
                    </div>`;
                } else {
                    output += `<div class="console-section">
                        <div class="console-message">No output produced</div>
                    </div>`;
                }
                
                if (response.error) {
                    output += `<div class="console-section">
                        <div class="console-label">Errors:</div>
                        <div class="error-line">${this.escapeHtml(response.error)}</div>
                    </div>`;
                }
                
                if (response.status) {
                    output += `<div class="console-section">
                        <div class="console-info">
                            Status: ${response.status.description || 'Completed'} | 
                            Time: ${response.time || 0}s | 
                            Memory: ${response.memory || 0}KB
                        </div>
                    </div>`;
                }
                
                consoleOutput.innerHTML = output;
            } else {
                consoleOutput.innerHTML = `<div class="error-line">${this.escapeHtml(response.error || 'Execution failed')}</div>`;
            }
        }

        displayExecutionError(error) {
            const consoleOutput = this.element.querySelector(`#console-output-${this.xblockId}`);
            consoleOutput.innerHTML = `<div class="error-line">${this.escapeHtml(error)}</div>`;
        }

        displaySubmissionResult(response) {
            const testResultsList = this.element.querySelector(`#test-results-${this.xblockId}`);
            const testSummary = this.element.querySelector(`#test-summary-${this.xblockId}`);
            
            // Update summary
            testSummary.innerHTML = `
                ${response.passed_tests}/${response.total_tests} tests passed | 
                Score: ${response.score.toFixed(1)}/${response.max_score}
            `;
            
            // Display test results
            let resultsHTML = '';
            response.test_results.forEach(test => {
                const statusClass = test.passed ? 'passed' : 'failed';
                const statusIcon = test.passed ? '✓' : '✗';
                
                resultsHTML += `
                    <div class="test-result-item ${statusClass}">
                        <div class="test-result-header">
                            <div class="test-result-name">${this.escapeHtml(test.name)}</div>
                            <div class="test-result-status ${statusClass}">
                                ${statusIcon} ${test.passed ? 'Passed' : 'Failed'}
                                <span class="test-result-points">${test.earned_points}/${test.points} pts</span>
                            </div>
                        </div>
                `;
                
                if (test.is_public) {
                    resultsHTML += `
                        <div class="test-result-details">
                            <div class="test-result-output">
                                <label>Expected Output:</label>
                                <pre>${this.escapeHtml(test.expected_output)}</pre>
                            </div>
                            <div class="test-result-output">
                                <label>Your Output:</label>
                                <pre>${this.escapeHtml(test.actual_output || '')}</pre>
                            </div>
                        </div>
                    `;
                }
                
                resultsHTML += '</div>';
            });
            
            testResultsList.innerHTML = resultsHTML;
        }

        setExecutionState(executing) {
            this.isExecuting = executing;
            const loadingOverlay = this.element.querySelector(`#loading-${this.xblockId}`);
            const buttons = this.element.querySelectorAll('.run-code-btn, .run-with-input-btn, .submit-solution-btn');
            
            if (executing) {
                loadingOverlay.style.display = 'flex';
                buttons.forEach(btn => btn.disabled = true);
            } else {
                loadingOverlay.style.display = 'none';
                buttons.forEach(btn => btn.disabled = false);
            }
        }

        switchOutputTab(tabName) {
            const tabs = this.element.querySelectorAll('.output-tab');
            const contents = this.element.querySelectorAll('.output-content');
            
            tabs.forEach(tab => {
                if (tab.getAttribute('data-tab') === tabName) {
                    tab.classList.add('active');
                } else {
                    tab.classList.remove('active');
                }
            });
            
            contents.forEach(content => {
                if (content.getAttribute('data-content') === tabName) {
                    content.classList.add('active');
                } else {
                    content.classList.remove('active');
                }
            });
        }

        clearConsole() {
            const consoleOutput = this.element.querySelector(`#console-output-${this.xblockId}`);
            consoleOutput.innerHTML = '<div class="console-message">Console cleared.</div>';
        }

        updateUI() {
            this.updateFileTabsUI();
            this.updateLanguageSelector();
            this.updateStatusBar();
        }

        updateFileTabsUI() {
            const tabs = this.element.querySelectorAll('.file-tab');
            tabs.forEach(tab => {
                const filename = tab.getAttribute('data-filename');
                if (filename === this.activeFile) {
                    tab.classList.add('active');
                } else {
                    tab.classList.remove('active');
                }
            });
        }

        updateLanguageSelector() {
            const selector = this.element.querySelector(`#language-select-${this.xblockId}`);
            if (selector) {
                selector.value = this.currentLanguage;
            }
        }

        updateStatusBar() {
            // Could add line/column info, etc.
        }

        updateScoreDisplay(currentScore, maxScore) {
            const currentScoreEl = this.element.querySelector('.current-score');
            if (currentScoreEl) {
                currentScoreEl.textContent = currentScore.toFixed(1);
            }
        }

        addFileTab(filename, language) {
            const tabsContainer = this.element.querySelector(`#file-tabs-${this.xblockId}`);
            const closeButton = Object.keys(this.studentFiles).length > 0 ? 
                `<button class="tab-close" data-filename="${filename}" title="Close file">×</button>` : '';
            
            const tabHTML = `
                <div class="file-tab" data-filename="${filename}" data-language="${language}">
                    <span class="tab-name">${this.escapeHtml(filename)}</span>
                    ${closeButton}
                </div>
            `;
            
            tabsContainer.insertAdjacentHTML('beforeend', tabHTML);
        }

        updateFileTab(oldFilename, newFilename) {
            const tab = this.element.querySelector(`[data-filename="${oldFilename}"]`);
            if (tab) {
                tab.setAttribute('data-filename', newFilename);
                const tabName = tab.querySelector('.tab-name');
                if (tabName) {
                    tabName.textContent = newFilename;
                }
                const closeBtn = tab.querySelector('.tab-close');
                if (closeBtn) {
                    closeBtn.setAttribute('data-filename', newFilename);
                }
            }
        }

        removeFileTab(filename) {
            const tab = this.element.querySelector(`[data-filename="${filename}"]`);
            if (tab) {
                tab.remove();
            }
        }

        handleKeyboardShortcuts(e) {
            // Ctrl/Cmd + S: Save
            if ((e.ctrlKey || e.metaKey) && e.key === 's') {
                e.preventDefault();
                this.saveCurrentFile();
            }
            
            // Ctrl/Cmd + R: Run
            if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
                e.preventDefault();
                this.runCode();
            }
            
            // Ctrl/Cmd + Enter: Submit
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                e.preventDefault();
                this.submitSolution();
            }
        }

        showNotification(type, message) {
            const notificationArea = this.element.querySelector(`#notifications-${this.xblockId}`);
            const notification = document.createElement('div');
            notification.className = `notification ${type}`;
            notification.textContent = message;
            
            notificationArea.appendChild(notification);
            
            // Auto-remove after 5 seconds
            setTimeout(() => {
                notification.remove();
            }, 5000);
        }

        callHandler(handlerName, data) {
            const handlerUrl = this.runtime.handlerUrl(this.element, handlerName);
            return $.post(handlerUrl, JSON.stringify(data))
                .then(response => {
                    if (typeof response === 'string') {
                        return JSON.parse(response);
                    }
                    return response;
                });
        }

        escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
    }

    // Initialize the XBlock when DOM is ready
    function AdvancedCodingXBlockInit(runtime, element) {
        const initArgsElement = $(element).find('.xblock-json-init-args');
        let initArgs = {};
        
        if (initArgsElement.length > 0) {
            try {
                initArgs = JSON.parse(initArgsElement.text());
            } catch (e) {
                console.error('Failed to parse init args:', e);
            }
        }
        
        return new AdvancedCodingXBlock(runtime, element, initArgs);
    }

    // Export for XBlock runtime
    window.AdvancedCodingXBlock = AdvancedCodingXBlockInit;
})();
