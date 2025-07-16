// AI SEO Assistant - Frontend JavaScript

class SEOAssistant {
    constructor() {
        this.apiUrl = 'http://127.0.0.1:8000';
        this.isLoading = false;
        this.currentStrategies = [];
        
        this.initializeElements();
        this.setupEventListeners();
        this.checkAPIHealth();
        this.loadRecentStrategies();
    }

    initializeElements() {
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.messages = document.getElementById('messages');
        this.loadingIndicator = document.getElementById('loadingIndicator');
        this.charCount = document.getElementById('charCount');
        this.statusIndicator = document.getElementById('statusIndicator');
        this.strategyCount = document.getElementById('strategyCount');
        this.sidebar = document.getElementById('sidebar');
        this.sidebarToggle = document.getElementById('sidebarToggle');
        this.closeSidebar = document.getElementById('closeSidebar');
        this.strategiesList = document.getElementById('strategiesList');
    }

    setupEventListeners() {
        // Send button click
        this.sendButton.addEventListener('click', () => this.sendMessage());
        
        // Enter key to send message
        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Auto-resize textarea
        this.messageInput.addEventListener('input', () => {
            this.updateCharCount();
            this.autoResizeTextarea();
            this.updateSendButton();
        });

        // Sidebar controls
        this.sidebarToggle.addEventListener('click', () => this.toggleSidebar());
        this.closeSidebar.addEventListener('click', () => this.closeSidebarPanel());

        // Click outside sidebar to close
        document.addEventListener('click', (e) => {
            if (this.sidebar.classList.contains('open') && 
                !this.sidebar.contains(e.target) && 
                !this.sidebarToggle.contains(e.target)) {
                this.closeSidebarPanel();
            }
        });
    }

    updateCharCount() {
        const count = this.messageInput.value.length;
        this.charCount.textContent = `${count} / 2000`;
        
        if (count > 1800) {
            this.charCount.style.color = 'var(--warning-color)';
        } else if (count > 1900) {
            this.charCount.style.color = 'var(--error-color)';
        } else {
            this.charCount.style.color = 'var(--text-muted)';
        }
    }

    autoResizeTextarea() {
        this.messageInput.style.height = 'auto';
        this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 120) + 'px';
    }

    updateSendButton() {
        const hasText = this.messageInput.value.trim().length > 0;
        this.sendButton.disabled = !hasText || this.isLoading;
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message || this.isLoading) return;

        try {
            this.isLoading = true;
            this.updateSendButton();
            
            // Add user message to chat
            this.addMessage(message, 'user');
            
            // Clear input
            this.messageInput.value = '';
            this.updateCharCount();
            this.autoResizeTextarea();
            
            // Show loading indicator
            this.showLoading();
            
            // Send to API
            const response = await this.callAPI('/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    question: message,
                    label: 'chat'
                })
            });

            // Hide loading indicator
            this.hideLoading();

            if (response.success) {
                // Add AI response to chat
                this.addMessage(response.response, 'ai');
                
                // Update strategy count
                this.loadRecentStrategies();
            } else {
                this.addMessage('I encountered an error processing your request. Please try again.', 'ai', true);
            }

        } catch (error) {
            console.error('Error sending message:', error);
            this.hideLoading();
            this.addMessage('Sorry, I\'m having trouble connecting. Please check your connection and try again.', 'ai', true);
        } finally {
            this.isLoading = false;
            this.updateSendButton();
        }
    }

    addMessage(text, sender, isError = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        const avatar = document.createElement('div');
        avatar.className = 'avatar';
        avatar.textContent = sender === 'user' ? '👤' : '🤖';
        
        const content = document.createElement('div');
        content.className = 'content';
        
        const textDiv = document.createElement('div');
        textDiv.className = 'text';
        if (isError) {
            textDiv.style.background = 'var(--error-color)';
            textDiv.style.color = 'white';
        }
        
        // Format text with basic markdown-like support
        textDiv.innerHTML = this.formatText(text);
        
        const timestamp = document.createElement('div');
        timestamp.className = 'timestamp';
        timestamp.textContent = new Date().toLocaleTimeString();
        
        content.appendChild(textDiv);
        content.appendChild(timestamp);
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(content);
        
        this.messages.appendChild(messageDiv);
        this.scrollToBottom();
    }

    formatText(text) {
        // Basic text formatting
        return text
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/^- (.*?)$/gm, '<li>$1</li>')
            .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
    }

    showLoading() {
        this.loadingIndicator.style.display = 'flex';
        this.scrollToBottom();
    }

    hideLoading() {
        this.loadingIndicator.style.display = 'none';
    }

    scrollToBottom() {
        setTimeout(() => {
            this.messages.scrollTop = this.messages.scrollHeight;
        }, 100);
    }

    toggleSidebar() {
        this.sidebar.classList.toggle('open');
        if (this.sidebar.classList.contains('open')) {
            this.loadRecentStrategies();
        }
    }

    closeSidebarPanel() {
        this.sidebar.classList.remove('open');
    }

    async checkAPIHealth() {
        try {
            const response = await this.callAPI('/health');
            if (response.status === 'healthy') {
                this.updateStatus('🟢 Online', 'var(--success-color)');
            } else {
                this.updateStatus('🟡 Degraded', 'var(--warning-color)');
            }
        } catch (error) {
            console.error('Health check failed:', error);
            this.updateStatus('🔴 Offline', 'var(--error-color)');
        }
    }

    updateStatus(text, color) {
        this.statusIndicator.textContent = text;
        this.statusIndicator.style.color = color;
    }

    async loadRecentStrategies() {
        try {
            const response = await this.callAPI('/strategies?limit=10');
            this.currentStrategies = response.strategies || [];
            this.updateStrategyCount();
            this.renderStrategies();
        } catch (error) {
            console.error('Error loading strategies:', error);
        }
    }

    updateStrategyCount() {
        const count = this.currentStrategies.length;
        this.strategyCount.textContent = `${count} strategies saved`;
    }

    renderStrategies() {
        this.strategiesList.innerHTML = '';
        
        if (this.currentStrategies.length === 0) {
            const emptyDiv = document.createElement('div');
            emptyDiv.style.textAlign = 'center';
            emptyDiv.style.color = 'var(--text-muted)';
            emptyDiv.style.padding = 'var(--spacing-lg)';
            emptyDiv.textContent = 'No strategies saved yet';
            this.strategiesList.appendChild(emptyDiv);
            return;
        }

        this.currentStrategies.forEach(strategy => {
            const strategyDiv = document.createElement('div');
            strategyDiv.className = 'strategy-item';
            
            const questionDiv = document.createElement('div');
            questionDiv.className = 'question';
            questionDiv.textContent = strategy.question;
            
            const timeDiv = document.createElement('div');
            timeDiv.className = 'time';
            timeDiv.textContent = this.formatTime(strategy.human_time);
            
            strategyDiv.appendChild(questionDiv);
            strategyDiv.appendChild(timeDiv);
            
            // Click to view strategy
            strategyDiv.addEventListener('click', () => {
                this.viewStrategy(strategy);
            });
            
            this.strategiesList.appendChild(strategyDiv);
        });
    }

    formatTime(timeString) {
        try {
            const date = new Date(timeString);
            const now = new Date();
            const diffMs = now - date;
            const diffMins = Math.floor(diffMs / 60000);
            
            if (diffMins < 1) return 'Just now';
            if (diffMins < 60) return `${diffMins}m ago`;
            if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
            if (diffMins < 10080) return `${Math.floor(diffMins / 1440)}d ago`;
            
            return date.toLocaleDateString();
        } catch (error) {
            return timeString;
        }
    }

    viewStrategy(strategy) {
        // Clear current messages
        this.messages.innerHTML = '';
        
        // Add the strategy conversation
        this.addMessage(strategy.question, 'user');
        this.addMessage(strategy.ai_response, 'ai');
        
        // Close sidebar
        this.closeSidebarPanel();
        
        // Add note about viewing saved strategy
        setTimeout(() => {
            const noteDiv = document.createElement('div');
            noteDiv.style.textAlign = 'center';
            noteDiv.style.color = 'var(--text-muted)';
            noteDiv.style.fontSize = '0.9rem';
            noteDiv.style.padding = 'var(--spacing-sm)';
            noteDiv.textContent = `Viewing saved strategy from ${this.formatTime(strategy.human_time)}`;
            this.messages.appendChild(noteDiv);
        }, 500);
    }

    async callAPI(endpoint, options = {}) {
        const url = `${this.apiUrl}${endpoint}`;
        const response = await fetch(url, options);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    }

    // Utility methods
    showError(message) {
        // Create error message element
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message show';
        errorDiv.textContent = message;
        
        // Insert at top of messages
        this.messages.insertBefore(errorDiv, this.messages.firstChild);
        
        // Remove after 5 seconds
        setTimeout(() => {
            errorDiv.remove();
        }, 5000);
    }

    // Initialize keyboard shortcuts
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + / to focus input
            if ((e.ctrlKey || e.metaKey) && e.key === '/') {
                e.preventDefault();
                this.messageInput.focus();
            }
            
            // Ctrl/Cmd + K to clear chat
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                this.clearChat();
            }
            
            // Ctrl/Cmd + S to toggle sidebar
            if ((e.ctrlKey || e.metaKey) && e.key === 's') {
                e.preventDefault();
                this.toggleSidebar();
            }
        });
    }

    clearChat() {
        this.messages.innerHTML = '';
        // Add welcome message back
        this.addMessage(`Hello! I'm your AI SEO assistant. I can help you:
        
• Analyze your YouTube channel performance
• Optimize video titles, descriptions, and tags
• Suggest content strategies based on trends
• Identify growth opportunities
• Create SEO-optimized content ideas

What would you like to know about your YouTube SEO strategy?`, 'ai');
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const app = new SEOAssistant();
    window.seoAssistant = app; // Make available globally for debugging
});

// Service Worker for offline support (optional)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then(registration => {
                console.log('SW registered: ', registration);
            })
            .catch(registrationError => {
                console.log('SW registration failed: ', registrationError);
            });
    });
} 