// planner/static/js/file_manager_header.js
class FileManagerHeaderSocket {
    constructor() {
        console.log('Initializing FileManagerHeaderSocket...');

        this.btn = document.getElementById('file_manager_btn');
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;

        if (!this.btn) {
            console.warn('File manager button not found in header. WebSocket not initialized.');
            return;
        }

        this.initWebSocket();
    }

    initWebSocket() {
        const wsScheme = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = wsScheme + '//' + window.location.host + '/ws/file-manager/';

        console.log('Connecting FileManager header WebSocket:', wsUrl);

        try {
            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                console.log('FileManager header WebSocket connected');
                this.reconnectAttempts = 0;
            };

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);

                    if (data.type === 'file_manager_status_update') {
                        this.updateButton(data.active_count, data.error_count);
                    } else if (data.type === 'connection_established') {
                        console.log('FileManager header WebSocket:', data.message);
                    }
                    // Остальные типы (progress_update, new_task) игнорируем — они для таблицы
                } catch (e) {
                    console.error('Error parsing FileManager header message:', e);
                }
            };

            this.ws.onclose = (event) => {
                console.log('FileManager header WebSocket disconnected:', event.code);
                this.reconnect();
            };

            this.ws.onerror = (error) => {
                console.error('FileManager header WebSocket error:', error);
            };
        } catch (e) {
            console.error('Error creating FileManager header WebSocket:', e);
            this.reconnect();
        }
    }

    reconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
            console.log(`FileManager header WebSocket reconnecting in ${delay}ms`);
            setTimeout(() => this.initWebSocket(), delay);
        }
    }

    updateButton(activeCount, errorCount) {
        if (!this.btn) return;

        // Удаляем все классы состояний
        this.btn.classList.remove('active-tasks', 'error-tasks', 'completed-tasks');

        if (errorCount > 0) {
            // Есть ошибки — красная обводка
            this.btn.classList.add('error-tasks');
        } else if (activeCount > 0) {
            // Есть активные задачи — синяя пульсация + анимированные стрелки
            this.btn.classList.add('active-tasks');
        } else {
            // Нет активных и нет ошибок — зелёная обводка (задачи завершены)
            // Проверяем, есть ли вообще хоть какие-то задачи
            this.btn.classList.add('completed-tasks');
        }
    }
}

// Инициализация при загрузке страницы
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        console.log('DOM loaded, initializing FileManagerHeaderSocket...');
        window.fileManagerHeaderSocket = new FileManagerHeaderSocket();
    });
} else {
    console.log('DOM already loaded, initializing FileManagerHeaderSocket...');
    window.fileManagerHeaderSocket = new FileManagerHeaderSocket();
}