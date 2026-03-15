class NotificationManager {
    constructor() {
        console.log('🔧 Initializing NotificationManager...');

        // Ищем контейнер
        this.container = document.getElementById('notification-container');

        // Если контейнер не найден, создаем его
        if (!this.container) {
            console.warn('⚠️ Notification container not found, creating one...');
            this.createContainer();
        } else {
            console.log('✅ Notification container found');
        }

        this.queue = [];
        this.isProcessing = false;
        this.activeToasts = new Set();
        this.maxVisible = 5; // Увеличим до 5
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.initWebSocket();
    }

    createContainer() {
        // Создаем контейнер в правом нижнем углу
        const container = document.createElement('div');
        container.id = 'notification-container';
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        container.style.zIndex = '9999';
        container.style.display = 'flex';
        container.style.flexDirection = 'column-reverse'; // Новые уведомления сверху
        container.style.gap = '10px';
        container.style.maxWidth = '350px';
        document.body.appendChild(container);
        this.container = container;
        console.log('✅ Notification container created in bottom-right corner');
    }

    initWebSocket() {
        const wsScheme = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = wsScheme + '//' + window.location.host + '/ws/notifications/';

        console.log('🔌 Connecting to WebSocket:', wsUrl);

        try {
            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                console.log('✅ WebSocket connected');
                this.reconnectAttempts = 0;
            };

            this.ws.onmessage = (event) => {
                console.log('📨 Raw message:', event.data);
                try {
                    const data = JSON.parse(event.data);
                    console.log('📨 Parsed message:', data);

                    if (data.type === 'notification') {
                        console.log('🔔 Got notification:', data.notification);
                        this.addToQueue(data.notification);
                    } else if (data.type === 'connection_established') {
                        console.log('🔌 Connection established:', data.message);
                    }
                } catch (e) {
                    console.error('Error parsing message:', e);
                }
            };

            this.ws.onclose = (event) => {
                console.log('❌ WebSocket disconnected:', event.code, event.reason);
                this.reconnect();
            };

            this.ws.onerror = (error) => {
                console.error('❌ WebSocket error:', error);
            };
        } catch (e) {
            console.error('Error creating WebSocket:', e);
            this.reconnect();
        }
    }

    reconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
            console.log(`🔄 Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
            setTimeout(() => this.initWebSocket(), delay);
        }
    }

    addToQueue(notification) {
        console.log('📥 Adding to queue:', notification);
        this.queue.push(notification);
        this.processQueue();
    }

    processQueue() {
        if (this.isProcessing || this.queue.length === 0) return;

        if (this.activeToasts.size >= this.maxVisible) {
            setTimeout(() => this.processQueue(), 500);
            return;
        }

        this.isProcessing = true;
        const notification = this.queue.shift();
        this.showToast(notification);
    }

    showToast(notification) {
        console.log('🖥️ Showing toast:', notification);

        // Дополнительная проверка контейнера
        if (!this.container) {
            console.error('❌ Container is null, creating again...');
            this.createContainer();

            if (!this.container) {
                console.error('❌ Failed to create container!');
                this.isProcessing = false;
                return;
            }
        }

        const toastId = 'toast-' + Date.now() + '-' + Math.random().toString(36).substring(2);

        // Определяем цвет для svg в зависимости от типа
        const svgColor = {
            'update': '#28a745', // зеленый
            'status': '#ffc107', // желтый
            'error': '#dc3545',   // красный
            'info': '#17a2b8'      // голубой
        }[notification.type] || '#007aff'; // синий по умолчанию

        // Форматируем время
        const time = new Date(notification.timestamp).toLocaleTimeString('ru-RU', {
            hour: '2-digit',
            minute: '2-digit'
        });

        const toastHtml = `
            <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true" data-bs-autohide="true" data-bs-delay="7000">
                <div class="toast-header">
                    <svg aria-hidden="true" class="rounded me-2" width="20" height="20" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg">
                        <rect width="100%" height="100%" fill="${svgColor}"></rect>
                    </svg>
                    <strong class="me-auto">${this.escapeHtml(notification.sender || 'System')}</strong>
                    <small class="text-body-secondary">${time}</small>
                    <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
                <div class="toast-body">
                    ${this.escapeHtml(notification.message)}
                    ${notification.comment ? `<br><small class="text-body-secondary">${this.escapeHtml(notification.comment)}</small>` : ''}
                </div>
            </div>
        `;

        // Вставляем HTML в начало контейнера
        this.container.insertAdjacentHTML('afterbegin', toastHtml);

        const toastElement = document.getElementById(toastId);
        toastElement.style.marginBottom = '10px';
        if (!toastElement) {
            console.error('❌ Toast element not found after insertion!');
            this.isProcessing = false;
            return;
        }

        // Проверяем наличие bootstrap
        if (typeof bootstrap === 'undefined') {
            console.error('❌ Bootstrap is not loaded!');
            this.isProcessing = false;
            return;
        }

        try {
            const toast = new bootstrap.Toast(toastElement, {
                autohide: true,
                delay: 7000
            });

            this.activeToasts.add(toastId);

            // Отмечаем как показанное
            this.markAsDisplayed(notification.recipient_id || notification.id);

            toastElement.addEventListener('hidden.bs.toast', () => {
                this.activeToasts.delete(toastId);
                toastElement.remove();
                this.isProcessing = false;
                this.processQueue();
            });

            toastElement.addEventListener('click', () => {
                this.markAsRead(notification.recipient_id || notification.id);
            }, { once: true });

            toast.show();
            console.log('✅ Toast shown successfully');

        } catch (e) {
            console.error('❌ Error showing toast:', e);
        }

        setTimeout(() => {
            this.isProcessing = false;
            this.processQueue();
        }, 300);
    }

    markAsDisplayed(notificationId) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                action: 'mark_as_displayed',
                notification_id: notificationId
            }));
        }
    }

    markAsRead(notificationId) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                action: 'mark_as_read',
                notification_id: notificationId
            }));
        }
    }

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Убедимся, что DOM загружен
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        console.log('🚀 DOM loaded, initializing NotificationManager...');
        window.notificationManager = new NotificationManager();
    });
} else {
    console.log('🚀 DOM already loaded, initializing NotificationManager...');
    window.notificationManager = new NotificationManager();
}