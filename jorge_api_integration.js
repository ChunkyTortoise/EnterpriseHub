/**
 * Jorge's Bot Command Center - API Integration
 * Provides real-time connectivity to Jorge's bot ecosystem
 */

class JorgeBotAPI {
    constructor() {
        this.baseURL = 'http://localhost:8002/api';
        this.websocketURL = 'ws://localhost:8002/ws';
        this.websocket = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.eventListeners = new Map();

        this.initializeConnection();
    }

    // WebSocket Connection Management
    async initializeConnection() {
        try {
            await this.connectWebSocket();
            await this.loadInitialData();
        } catch (error) {
            console.error('Failed to initialize Jorge API connection:', error);
        }
    }

    async connectWebSocket() {
        return new Promise((resolve, reject) => {
            try {
                this.websocket = new WebSocket(this.websocketURL);

                this.websocket.onopen = () => {
                    console.log('Connected to Jorge Bot WebSocket');
                    this.isConnected = true;
                    this.reconnectAttempts = 0;
                    this.updateConnectionStatus(true);
                    resolve();
                };

                this.websocket.onmessage = (event) => {
                    this.handleWebSocketMessage(event);
                };

                this.websocket.onclose = () => {
                    console.log('Jorge Bot WebSocket connection closed');
                    this.isConnected = false;
                    this.updateConnectionStatus(false);
                    this.attemptReconnection();
                };

                this.websocket.onerror = (error) => {
                    console.error('Jorge Bot WebSocket error:', error);
                    reject(error);
                };

            } catch (error) {
                reject(error);
            }
        });
    }

    handleWebSocketMessage(event) {
        try {
            const message = JSON.parse(event.data);
            this.emit('message', message);

            // Handle specific event types
            switch (message.type) {
                case 'bot_status_update':
                    this.emit('bot_status', message.data);
                    break;
                case 'jorge_qualification_progress':
                    this.emit('qualification_progress', message.data);
                    break;
                case 'conversation_update':
                    this.emit('conversation_update', message.data);
                    break;
                case 'claude_concierge_insight':
                    this.emit('claude_insight', message.data);
                    break;
                default:
                    console.log('Received unknown message type:', message.type);
            }
        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
        }
    }

    attemptReconnection() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);

            console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

            setTimeout(() => {
                this.connectWebSocket();
            }, delay);
        } else {
            console.error('Max reconnection attempts reached. Please refresh the page.');
            this.updateConnectionStatus(false, 'Connection failed');
        }
    }

    updateConnectionStatus(connected, message = null) {
        const statusElement = document.querySelector('.status-indicator');
        const statusDot = document.querySelector('.status-dot');
        const statusText = statusElement.querySelector('span');

        if (connected) {
            statusDot.style.background = '#22c55e';
            statusText.textContent = 'All Systems Operational';
            statusElement.style.background = 'rgba(34, 197, 94, 0.2)';
            statusElement.style.border = '1px solid rgba(34, 197, 94, 0.3)';
        } else {
            statusDot.style.background = '#ef4444';
            statusText.textContent = message || 'Connection Issues';
            statusElement.style.background = 'rgba(239, 68, 68, 0.2)';
            statusElement.style.border = '1px solid rgba(239, 68, 68, 0.3)';
        }
    }

    // Event System
    on(event, callback) {
        if (!this.eventListeners.has(event)) {
            this.eventListeners.set(event, []);
        }
        this.eventListeners.get(event).push(callback);
    }

    emit(event, data) {
        if (this.eventListeners.has(event)) {
            this.eventListeners.get(event).forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in event listener for ${event}:`, error);
                }
            });
        }
    }

    // API Methods - Jorge Seller Bot
    async sendSellerMessage(contactId, message, contactInfo = null) {
        try {
            const response = await fetch(`${this.baseURL}/jorge-seller/process`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    contact_id: contactId,
                    location_id: 'austin_office',
                    message: message,
                    contact_info: contactInfo || {
                        name: 'Demo Client',
                        phone: '+1234567890',
                        email: 'demo@example.com'
                    }
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error sending seller message:', error);
            throw error;
        }
    }

    async getSellerBotStatus() {
        try {
            const response = await fetch(`${this.baseURL}/bots/jorge-seller/status`);
            return await response.json();
        } catch (error) {
            console.error('Error getting seller bot status:', error);
            throw error;
        }
    }

    async applyStallBreaker(leadId, stallType) {
        try {
            const response = await fetch(`${this.baseURL}/jorge-seller/${leadId}/stall-breaker`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    stall_type: stallType
                })
            });

            return await response.json();
        } catch (error) {
            console.error('Error applying stall breaker:', error);
            throw error;
        }
    }

    // API Methods - Lead Bot
    async getLeadSequenceStatus(leadId) {
        try {
            const response = await fetch(`${this.baseURL}/lead-bot/${leadId}/sequence-status`);
            return await response.json();
        } catch (error) {
            console.error('Error getting lead sequence status:', error);
            throw error;
        }
    }

    async scheduleFollowUp(leadId, sequenceDay) {
        try {
            const response = await fetch(`${this.baseURL}/lead-bot/${leadId}/schedule`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    sequenceDay: sequenceDay
                })
            });

            return await response.json();
        } catch (error) {
            console.error('Error scheduling follow-up:', error);
            throw error;
        }
    }

    // API Methods - Buyer Bot
    async processBuyerMessage(contactId, message, preferences = null) {
        try {
            const response = await fetch(`${this.baseURL}/buyer-bot/process`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    contact_id: contactId,
                    message: message,
                    preferences: preferences
                })
            });

            return await response.json();
        } catch (error) {
            console.error('Error processing buyer message:', error);
            throw error;
        }
    }

    // API Methods - Claude Concierge
    async askClaude(question, context = null) {
        try {
            const response = await fetch(`${this.baseURL}/claude-concierge/ask`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    question: question,
                    context: context,
                    mode: 'omnipresent'
                })
            });

            return await response.json();
        } catch (error) {
            console.error('Error asking Claude:', error);
            throw error;
        }
    }

    async getClaudeInsights() {
        try {
            const response = await fetch(`${this.baseURL}/claude-concierge/insights`);
            return await response.json();
        } catch (error) {
            console.error('Error getting Claude insights:', error);
            throw error;
        }
    }

    // API Methods - Analytics
    async getBotMetrics() {
        try {
            const response = await fetch(`${this.baseURL}/analytics/bot-metrics`);
            return await response.json();
        } catch (error) {
            console.error('Error getting bot metrics:', error);
            throw error;
        }
    }

    async getPerformanceData(timeframe = '24h') {
        try {
            const response = await fetch(`${this.baseURL}/analytics/performance?timeframe=${timeframe}`);
            return await response.json();
        } catch (error) {
            console.error('Error getting performance data:', error);
            throw error;
        }
    }

    // Utility Methods
    async loadInitialData() {
        try {
            // Load bot statuses
            const [botMetrics, claudeInsights] = await Promise.all([
                this.getBotMetrics(),
                this.getClaudeInsights()
            ]);

            this.emit('initial_data_loaded', {
                botMetrics,
                claudeInsights
            });

        } catch (error) {
            console.error('Error loading initial data:', error);
        }
    }

    // Schedule appointment via API
    async scheduleAppointment(appointmentData) {
        try {
            const response = await fetch(`${this.baseURL}/appointments/schedule`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(appointmentData)
            });

            return await response.json();
        } catch (error) {
            console.error('Error scheduling appointment:', error);
            throw error;
        }
    }

    // Get active conversations
    async getActiveConversations() {
        try {
            const response = await fetch(`${this.baseURL}/conversations/active`);
            return await response.json();
        } catch (error) {
            console.error('Error getting active conversations:', error);
            throw error;
        }
    }

    // Close connection
    disconnect() {
        if (this.websocket) {
            this.websocket.close();
        }
        this.isConnected = false;
    }
}

// Enhanced UI Controller
class JorgeCommandCenter {
    constructor() {
        this.api = new JorgeBotAPI();
        this.currentConversations = new Map();
        this.setupEventListeners();
        this.setupAPIEventListeners();
    }

    setupEventListeners() {
        // Enhanced message sending with real API integration
        document.addEventListener('DOMContentLoaded', () => {
            this.initializeUI();
        });
    }

    setupAPIEventListeners() {
        // Real-time bot status updates
        this.api.on('bot_status', (data) => {
            this.updateBotStatus(data);
        });

        // Qualification progress updates
        this.api.on('qualification_progress', (data) => {
            this.updateQualificationProgress(data);
        });

        // Conversation updates
        this.api.on('conversation_update', (data) => {
            this.updateConversation(data);
        });

        // Claude insights
        this.api.on('claude_insight', (data) => {
            this.displayClaudeInsight(data);
        });

        // Initial data loading
        this.api.on('initial_data_loaded', (data) => {
            this.populateInitialData(data);
        });
    }

    initializeUI() {
        // Enhanced seller message functionality
        this.setupEnhancedSellerChat();
        this.setupClaudeIntegration();
        this.setupRealTimeMetrics();
    }

    setupEnhancedSellerChat() {
        const messageInput = document.getElementById('seller-message');
        const sendButton = document.querySelector('#seller-bot .btn');

        // Enhanced send function with real API
        window.sendSellerMessage = async () => {
            const message = messageInput.value.trim();
            if (!message) return;

            // Add message to UI immediately
            this.addMessageToConversation('seller-conversation', 'user', message);
            messageInput.value = '';

            // Add loading indicator
            const loadingId = this.addLoadingMessage('seller-conversation');

            try {
                const result = await this.api.sendSellerMessage(
                    'demo_client_123',
                    message,
                    {
                        name: 'Demo Client',
                        phone: '+1234567890',
                        email: 'demo@example.com'
                    }
                );

                // Remove loading and add response
                this.removeLoadingMessage('seller-conversation', loadingId);
                this.addMessageToConversation('seller-conversation', 'bot', result.response_message);

                // Update metrics
                this.updateSellerMetrics(result);

                // Add real-time update
                this.addRealtimeUpdate(`Seller qualification updated - ${result.seller_temperature} lead`);

            } catch (error) {
                this.removeLoadingMessage('seller-conversation', loadingId);
                this.addMessageToConversation('seller-conversation', 'bot',
                    'Sorry, I\'m having technical difficulties. Let me get back to you.', 'error');
            }
        };
    }

    setupClaudeIntegration() {
        // Enhanced Claude chat functionality
        const claudeChatInput = document.querySelector('#claude-chat input');
        const claudeSendButton = document.querySelector('#claude-chat .btn');

        if (claudeChatInput && claudeSendButton) {
            claudeSendButton.onclick = () => this.sendClaudeMessage();
            claudeChatInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') this.sendClaudeMessage();
            });
        }
    }

    async sendClaudeMessage() {
        const input = document.querySelector('#claude-chat input');
        const message = input.value.trim();
        if (!message) return;

        // Add user message to Claude chat
        const chatBody = document.querySelector('.claude-chat-body');
        this.addMessageToClaude(chatBody, 'user', message);
        input.value = '';

        // Add loading indicator
        const loadingId = this.addLoadingMessage('claude-chat-body');

        try {
            const response = await this.api.askClaude(message, {
                currentTab: this.getCurrentTab(),
                activeConversations: Array.from(this.currentConversations.keys())
            });

            this.removeLoadingMessage('claude-chat-body', loadingId);
            this.addMessageToClaude(chatBody, 'bot', response.response);

        } catch (error) {
            this.removeLoadingMessage('claude-chat-body', loadingId);
            this.addMessageToClaude(chatBody, 'bot',
                'I\'m having trouble connecting right now. Please try again.', 'error');
        }
    }

    setupRealTimeMetrics() {
        // Update metrics every 30 seconds
        setInterval(async () => {
            try {
                const metrics = await this.api.getBotMetrics();
                this.updateDashboardMetrics(metrics);
            } catch (error) {
                console.error('Error updating metrics:', error);
            }
        }, 30000);
    }

    // UI Helper Methods
    addMessageToConversation(panelId, sender, message, type = 'normal') {
        const panel = document.getElementById(panelId);
        const messageElement = document.createElement('div');
        messageElement.className = `message ${sender}`;

        if (type === 'error') {
            messageElement.style.borderColor = 'rgba(239, 68, 68, 0.3)';
            messageElement.style.background = 'rgba(239, 68, 68, 0.1)';
        }

        const senderName = sender === 'user' ? 'You' : 'Jorge';
        messageElement.innerHTML = `<strong>${senderName}:</strong> ${message}`;

        panel.appendChild(messageElement);
        panel.scrollTop = panel.scrollHeight;

        return messageElement;
    }

    addMessageToClaude(chatBody, sender, message, type = 'normal') {
        const messageElement = document.createElement('div');
        messageElement.className = `message ${sender}`;

        if (type === 'error') {
            messageElement.style.borderColor = 'rgba(239, 68, 68, 0.3)';
            messageElement.style.background = 'rgba(239, 68, 68, 0.1)';
        }

        const senderName = sender === 'user' ? 'You' : 'Claude';
        messageElement.innerHTML = `<strong>${senderName}:</strong> ${message}`;

        chatBody.appendChild(messageElement);
        chatBody.scrollTop = chatBody.scrollHeight;

        return messageElement;
    }

    addLoadingMessage(panelId) {
        const panel = document.getElementById(panelId) || document.querySelector(`.${panelId}`);
        const loadingElement = document.createElement('div');
        const loadingId = 'loading_' + Date.now();
        loadingElement.id = loadingId;
        loadingElement.className = 'message bot';
        loadingElement.innerHTML = '<strong>Processing:</strong> <span class="loading"></span> Please wait...';

        panel.appendChild(loadingElement);
        panel.scrollTop = panel.scrollHeight;

        return loadingId;
    }

    removeLoadingMessage(panelId, loadingId) {
        const loadingElement = document.getElementById(loadingId);
        if (loadingElement) {
            loadingElement.remove();
        }
    }

    updateSellerMetrics(result) {
        // Update temperature gauge
        const tempGauge = document.querySelector('.temperature-inner');
        if (tempGauge) {
            tempGauge.textContent = result.seller_temperature.toUpperCase();
        }

        // Update FRS/PCS scores
        if (result.analytics) {
            const metricValues = document.querySelectorAll('.metric-value');
            if (metricValues[0]) {
                metricValues[0].textContent = Math.round(result.analytics.frs_score || 0) + '%';
            }
            if (metricValues[1]) {
                metricValues[1].textContent = Math.round(result.analytics.pcs_score || 0) + '%';
            }
        }
    }

    updateBotStatus(data) {
        // Update bot status indicators across the interface
        const statusIndicators = document.querySelectorAll('.bot-status');
        statusIndicators.forEach(indicator => {
            if (indicator.dataset.botType === data.bot_type) {
                indicator.textContent = data.status;
                indicator.className = `bot-status ${data.status}`;
            }
        });
    }

    updateQualificationProgress(data) {
        // Update qualification progress indicators
        const progressElements = document.querySelectorAll('.qualification-progress');
        progressElements.forEach(element => {
            if (element.dataset.contactId === data.contact_id) {
                element.textContent = `${data.questions_answered}/4 questions`;
            }
        });
    }

    updateConversation(data) {
        // Handle real-time conversation updates
        if (data.stage === 'response_generated') {
            this.addRealtimeUpdate(`New response generated for ${data.lead_id}`);
        }
    }

    displayClaudeInsight(data) {
        // Display Claude insights in the interface
        const insightElement = document.querySelector('.ai-insight p');
        if (insightElement) {
            insightElement.textContent = data.insight;
        }
    }

    populateInitialData(data) {
        // Populate dashboard with initial data
        this.updateDashboardMetrics(data.botMetrics);

        // Display initial Claude insights
        if (data.claudeInsights) {
            this.displayClaudeInsight(data.claudeInsights);
        }
    }

    updateDashboardMetrics(metrics) {
        // Update various dashboard metrics
        const metricElements = document.querySelectorAll('[data-metric]');
        metricElements.forEach(element => {
            const metricType = element.dataset.metric;
            if (metrics[metricType]) {
                element.textContent = metrics[metricType];
            }
        });
    }

    getCurrentTab() {
        const activeTab = document.querySelector('.tab.active');
        return activeTab ? activeTab.textContent.trim() : 'seller-bot';
    }

    addRealtimeUpdate(message) {
        const updatesPanel = document.querySelector('.real-time-updates');
        if (!updatesPanel) return;

        const updateItem = document.createElement('div');
        updateItem.className = 'update-item';
        const now = new Date();
        updateItem.innerHTML = `<strong>${now.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</strong> - ${message}`;

        // Add to top
        const firstUpdate = updatesPanel.querySelector('.update-item');
        if (firstUpdate) {
            updatesPanel.insertBefore(updateItem, firstUpdate);
        } else {
            updatesPanel.appendChild(updateItem);
        }

        // Keep only last 5 updates
        const updates = updatesPanel.querySelectorAll('.update-item');
        if (updates.length > 5) {
            updatesPanel.removeChild(updates[updates.length - 1]);
        }
    }

    // Enhanced appointment scheduling
    async scheduleAppointmentAPI(appointmentData) {
        try {
            const result = await this.api.scheduleAppointment(appointmentData);
            this.addRealtimeUpdate(`Appointment scheduled: ${appointmentData.clientName} - ${appointmentData.type}`);
            return result;
        } catch (error) {
            console.error('Error scheduling appointment:', error);
            throw error;
        }
    }
}

// Initialize the command center when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.jorgeCommandCenter = new JorgeCommandCenter();
    console.log('Jorge Bot Command Center initialized');
});

// Enhanced global functions
window.applyStallBreaker = async function() {
    try {
        const result = await window.jorgeCommandCenter.api.applyStallBreaker('demo_client_123', 'thinking');
        window.jorgeCommandCenter.addMessageToConversation('seller-conversation', 'bot',
            result.response || 'Look, I\'m going to be straight with you. Either you\'re serious about selling or you\'re not. Which is it?');
        window.jorgeCommandCenter.addRealtimeUpdate('Stall breaker applied to active lead');
    } catch (error) {
        console.error('Error applying stall breaker:', error);
    }
};

window.confirmAppointment = async function() {
    const client = document.getElementById('appointment-client').value;
    const type = document.getElementById('appointment-type').value;
    const datetime = document.getElementById('appointment-datetime').value;

    if (client && datetime) {
        try {
            const appointmentData = {
                clientName: client,
                type: type,
                datetime: datetime,
                notes: document.querySelector('#schedule-modal textarea').value
            };

            await window.jorgeCommandCenter.scheduleAppointmentAPI(appointmentData);

            alert(`Appointment scheduled successfully!\nClient: ${client}\nType: ${type}\nDate: ${new Date(datetime).toLocaleString()}`);
            closeScheduleModal();

            // Clear form
            document.getElementById('appointment-client').value = '';
            document.getElementById('appointment-datetime').value = '';
            document.querySelector('#schedule-modal textarea').value = '';

        } catch (error) {
            alert('Error scheduling appointment. Please try again.');
            console.error('Appointment scheduling error:', error);
        }
    }
};