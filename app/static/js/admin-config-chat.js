/**
 * Admin Configuration Agent - Chat Interface Component
 * Allows SuperAdmins to manage agents, app, and infrastructure via natural language
 */

class AdminConfigChat {
    constructor() {
        this.chatContainer = null;
        this.inputField = null;
        this.messagesContainer = null;
        this.isProcessing = false;
    }

    /**
     * Initialize the admin config chat interface
     */
    init() {
        this.createChatInterface();
        this.attachEventListeners();
        this.loadConfigHistory();
    }

    /**
     * Create the chat interface HTML
     */
    createChatInterface() {
        const container = document.createElement('div');
        container.className = 'admin-config-chat-container';
        container.innerHTML = `
            <div class="config-chat-header">
                <h3>
                    <i class="fas fa-robot"></i>
                    Configuration Assistant
                </h3>
                <button class="btn-help" onclick="adminConfigChat.showHelp()">
                    <i class="fas fa-question-circle"></i> Help
                </button>
            </div>
            
            <div class="config-chat-messages" id="configChatMessages">
                <div class="welcome-message">
                    <p><strong>Welcome to the Configuration Assistant!</strong></p>
                    <p>I can help you manage agents, application settings, and infrastructure using natural language.</p>
                    <div class="example-commands">
                        <p><strong>Try commands like:</strong></p>
                        <ul>
                            <li>"Update SalesAssistant to focus on Azure products"</li>
                            <li>"Add web_search tool to AnalyticsAssistant"</li>
                            <li>"Disable the FinancialAdvisor agent"</li>
                            <li>"List all agent configurations"</li>
                            <li>"Change max request timeout to 120 seconds"</li>
                        </ul>
                    </div>
                </div>
            </div>
            
            <div class="config-chat-input-container">
                <textarea 
                    id="configChatInput" 
                    class="config-chat-input" 
                    placeholder="Type a configuration command... (e.g., 'Update SalesAssistant prompt')"
                    rows="2"
                ></textarea>
                <button 
                    id="configChatSend" 
                    class="btn btn-primary config-chat-send"
                >
                    <i class="fas fa-paper-plane"></i> Send
                </button>
            </div>
            
            <div class="config-chat-footer">
                <button class="btn btn-sm btn-secondary" onclick="adminConfigChat.showHistory()">
                    <i class="fas fa-history"></i> History
                </button>
                <button class="btn btn-sm btn-warning" onclick="adminConfigChat.showRollback()">
                    <i class="fas fa-undo"></i> Rollback
                </button>
            </div>
        `;

        this.chatContainer = container;
        this.messagesContainer = container.querySelector('#configChatMessages');
        this.inputField = container.querySelector('#configChatInput');
        
        return container;
    }

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        const sendButton = this.chatContainer.querySelector('#configChatSend');
        sendButton.addEventListener('click', () => this.sendMessage());
        
        this.inputField.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
    }

    /**
     * Send configuration message
     */
    async sendMessage() {
        if (this.isProcessing) return;
        
        const message = this.inputField.value.trim();
        if (!message) return;
        
        // Add user message to chat
        this.addMessage('user', message);
        this.inputField.value = '';
        this.isProcessing = true;
        
        // Show typing indicator
        const typingId = this.showTypingIndicator();
        
        try {
            const response = await fetch('/api/admin/agents/config/natural-update', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify({ request: message })
            });
            
            const result = await response.json();
            
            // Remove typing indicator
            this.removeTypingIndicator(typingId);
            
            if (result.success) {
                this.addSuccessMessage(result);
            } else {
                this.addErrorMessage(result.message || 'Configuration update failed');
            }
            
        } catch (error) {
            this.removeTypingIndicator(typingId);
            this.addErrorMessage(`Error: ${error.message}`);
        } finally {
            this.isProcessing = false;
        }
    }

    /**
     * Add message to chat
     */
    addMessage(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `config-message config-message-${role}`;
        
        const timestamp = new Date().toLocaleTimeString();
        
        messageDiv.innerHTML = `
            <div class="message-header">
                <strong>${role === 'user' ? 'You' : 'Assistant'}</strong>
                <span class="message-time">${timestamp}</span>
            </div>
            <div class="message-content">${this.formatMessage(content)}</div>
        `;
        
        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }

    /**
     * Add success message with details
     */
    addSuccessMessage(result) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'config-message config-message-assistant success';
        
        let content = `<div class="success-icon"><i class="fas fa-check-circle"></i></div>`;
        content += `<p><strong>${result.message}</strong></p>`;
        
        if (result.changes) {
            content += '<div class="changes-summary"><strong>Changes Applied:</strong><ul>';
            for (const [key, value] of Object.entries(result.changes)) {
                content += `<li><code>${key}</code>: ${JSON.stringify(value)}</li>`;
            }
            content += '</ul></div>';
        }
        
        if (result.note) {
            content += `<div class="config-note"><i class="fas fa-info-circle"></i> ${result.note}</div>`;
        }
        
        if (result.deployment_command) {
            content += `<div class="deployment-command">
                <strong>Deployment Command:</strong>
                <pre><code>${result.deployment_command}</code></pre>
                <button class="btn btn-sm btn-secondary" onclick="adminConfigChat.copyToClipboard(\`${result.deployment_command.replace(/`/g, '\\`')}\`)">
                    <i class="fas fa-copy"></i> Copy
                </button>
            </div>`;
        }
        
        if (result.configurations) {
            content += '<div class="config-list">';
            for (const [category, config] of Object.entries(result.configurations)) {
                content += `<details>
                    <summary><strong>${category}</strong></summary>
                    <pre><code>${JSON.stringify(config, null, 2)}</code></pre>
                </details>`;
            }
            content += '</div>';
        }
        
        messageDiv.innerHTML = content;
        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }

    /**
     * Add error message
     */
    addErrorMessage(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'config-message config-message-assistant error';
        messageDiv.innerHTML = `
            <div class="error-icon"><i class="fas fa-exclamation-circle"></i></div>
            <p>${message}</p>
        `;
        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }

    /**
     * Show typing indicator
     */
    showTypingIndicator() {
        const id = 'typing-' + Date.now();
        const indicator = document.createElement('div');
        indicator.id = id;
        indicator.className = 'config-message config-message-assistant typing';
        indicator.innerHTML = `
            <div class="typing-indicator">
                <span></span><span></span><span></span>
            </div>
        `;
        this.messagesContainer.appendChild(indicator);
        this.scrollToBottom();
        return id;
    }

    /**
     * Remove typing indicator
     */
    removeTypingIndicator(id) {
        const indicator = document.getElementById(id);
        if (indicator) {
            indicator.remove();
        }
    }

    /**
     * Format message content
     */
    formatMessage(content) {
        // Convert markdown-style code blocks
        content = content.replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>');
        
        // Convert inline code
        content = content.replace(/`([^`]+)`/g, '<code>$1</code>');
        
        // Convert line breaks
        content = content.replace(/\n/g, '<br>');
        
        return content;
    }

    /**
     * Scroll to bottom of messages
     */
    scrollToBottom() {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }

    /**
     * Show help dialog
     */
    showHelp() {
        const helpContent = `
            <h4>Configuration Assistant Help</h4>
            
            <h5>Agent Management</h5>
            <ul>
                <li>"Update [agent] display name to '[name]'"</li>
                <li>"Change [agent] prompt to focus on [topic]"</li>
                <li>"Add [tool] tool to [agent]"</li>
                <li>"Enable/Disable [agent]"</li>
                <li>"List all agents"</li>
            </ul>
            
            <h5>App Configuration</h5>
            <ul>
                <li>"Change max request timeout to [seconds] seconds"</li>
                <li>"Enable/Disable debug logging"</li>
                <li>"Update rate limit to [number] requests per hour"</li>
                <li>"Show app configuration"</li>
            </ul>
            
            <h5>Infrastructure</h5>
            <ul>
                <li>"Scale web app to [number] instances"</li>
                <li>"Enable auto-scaling from [min] to [max] instances"</li>
                <li>"Update database tier to [tier]"</li>
                <li>"Show infrastructure configuration"</li>
            </ul>
            
            <h5>Available Agents</h5>
            <ul>
                <li><strong>sales</strong> - SalesAssistant</li>
                <li><strong>analytics</strong> - AnalyticsAssistant</li>
                <li><strong>financial</strong> - FinancialAdvisor</li>
                <li><strong>operations</strong> - OperationsAssistant</li>
                <li><strong>support</strong> - SupportAssistant</li>
            </ul>
        `;
        
        this.showModal('Help', helpContent);
    }

    /**
     * Show configuration history
     */
    async showHistory() {
        try {
            const response = await fetch('/api/admin/agents/config/history?limit=20', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });
            
            const result = await response.json();
            
            if (result.success && result.changes) {
                let historyHTML = '<h4>Recent Configuration Changes</h4>';
                historyHTML += '<div class="history-list">';
                
                result.changes.forEach(change => {
                    historyHTML += `
                        <div class="history-item">
                            <div class="history-header">
                                <span class="badge badge-${change.category}">${change.category}</span>
                                <strong>${change.target}</strong>
                                <span class="history-time">${new Date(change.timestamp).toLocaleString()}</span>
                            </div>
                            <p>${change.change_summary}</p>
                            <small>By: ${change.changed_by}</small>
                            ${change.rollback_available ? `
                                <button class="btn btn-sm btn-warning" onclick="adminConfigChat.rollback(${change.id})">
                                    <i class="fas fa-undo"></i> Rollback
                                </button>
                            ` : ''}
                        </div>
                    `;
                });
                
                historyHTML += '</div>';
                this.showModal('Configuration History', historyHTML);
            }
        } catch (error) {
            this.addErrorMessage(`Failed to load history: ${error.message}`);
        }
    }

    /**
     * Show rollback interface
     */
    showRollback() {
        this.showHistory(); // Reuse history view with rollback buttons
    }

    /**
     * Rollback a configuration change
     */
    async rollback(changeId) {
        if (!confirm('Are you sure you want to rollback this configuration change?')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/admin/agents/config/rollback/${changeId}`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.addSuccessMessage(result);
                this.closeModal();
            } else {
                this.addErrorMessage(result.message || 'Rollback failed');
            }
        } catch (error) {
            this.addErrorMessage(`Rollback error: ${error.message}`);
        }
    }

    /**
     * Copy text to clipboard
     */
    copyToClipboard(text) {
        navigator.clipboard.writeText(text).then(() => {
            // Show toast notification
            this.showToast('Copied to clipboard!');
        });
    }

    /**
     * Show toast notification
     */
    showToast(message) {
        const toast = document.createElement('div');
        toast.className = 'toast-notification';
        toast.textContent = message;
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.classList.add('show');
        }, 10);
        
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    /**
     * Show modal dialog
     */
    showModal(title, content) {
        const modal = document.createElement('div');
        modal.className = 'config-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>${title}</h3>
                    <button class="modal-close" onclick="adminConfigChat.closeModal()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-body">
                    ${content}
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        setTimeout(() => modal.classList.add('show'), 10);
    }

    /**
     * Close modal dialog
     */
    closeModal() {
        const modal = document.querySelector('.config-modal');
        if (modal) {
            modal.classList.remove('show');
            setTimeout(() => modal.remove(), 300);
        }
    }

    /**
     * Load configuration history on init
     */
    async loadConfigHistory() {
        // Optionally load recent changes
    }
}

// Initialize global instance
const adminConfigChat = new AdminConfigChat();

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        // Will be initialized by admin page
    });
}
