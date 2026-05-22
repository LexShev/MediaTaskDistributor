// planner/static/js/file_manager.js
class FileManager {
    constructor() {
        this.container = document.getElementById('file_manager_container');
        this.searchInput = document.getElementById('search_input');
        this.statusFilter = document.getElementById('status_filter');
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;

        this.init();
    }

    init() {
        // Загружаем начальные данные
        this.loadFileManager();

        // Инициализируем WebSocket
        this.initWebSocket();

        // Обработчики событий
        this.setupEventListeners();

        // Автообновление (если WebSocket не работает)
        // this.startPolling();
    }

    setupEventListeners() {
        // Поиск по Enter
        if (this.searchInput) {
            this.searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.loadFileManager();
                }
            });
        }

        // Фильтр статуса
        if (this.statusFilter) {
            this.statusFilter.addEventListener('change', () => {
                this.loadFileManager();
            });
        }
    }

    initWebSocket() {
        const wsScheme = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = wsScheme + '//' + window.location.host + '/ws/file-manager/';

        console.log('Connecting to FileManager WebSocket:', wsUrl);

        try {
            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                console.log('FileManager WebSocket connected');
                this.reconnectAttempts = 0;
            };

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);

                    if (data.type === 'progress_update') {
                        this.updateTaskProgress(data);
                    } else if (data.type === 'new_task') {
                    // Новая задача — перезагружаем таблицу
                    console.log('New task detected:', data?.file_name);
                    this.loadFileManager();  // сохраняет текущую страницу

                    } else if (data.type === 'connection_established') {
                        console.log('FileManager WebSocket:', data.message);
                    }
                } catch (e) {
                    console.error('Error parsing WebSocket message:', e);
                }
            };

            this.ws.onclose = (event) => {
                console.log('FileManager WebSocket disconnected:', event.code);
                this.reconnect();
            };

            this.ws.onerror = (error) => {
                console.error('FileManager WebSocket error:', error);
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
            console.log(`FileManager WebSocket reconnecting in ${delay}ms`);
            setTimeout(() => this.initWebSocket(), delay);
        }
    }

    updateTaskProgress(data) {
        console.log('Received progress update:', data);

        // Ищем строку по data-task-id
        const taskRow = document.querySelector(`tr[data-task-id="${data.task_id}"]`);

        if (!taskRow) {
            // Если строка не найдена, возможно, она на другой странице.
            // Можно не перезагружать всё, а просто ждать.
            // Но если это новая задача на текущей странице - перезагружаем.
            // В этой версии мы не будем автоматически перезагружать, чтобы не было мерцания.
            console.warn(`Task row not found for task_id=${data.task_id}`);
            return;
        }

        // 1. Обновляем статус (badge)
        const statusBadge = taskRow.querySelector('.status-badge');
        if (statusBadge && data.status) {
            // Маппинг статусов на классы Bootstrap
            const statusClasses = {
                'pending': 'text-secondary-emphasis bg-secondary-subtle',
                'copying': 'text-primary-emphasis bg-primary-subtle',
                'verifying': 'text-warning-emphasis bg-warning-subtle',
                'completed': 'text-success-emphasis bg-success-subtle',
                'error': 'text-danger-emphasis bg-danger-subtle'
            };
            const statusTexts = {
                'pending': 'Ожидает',
                'copying': 'Копирование',
                'verifying': 'Проверка',
                'completed': 'Завершено',
                'error': 'Ошибка'
            };

            // Очищаем текущие классы статуса и добавляем новые
            statusBadge.className = `badge status-badge ${statusClasses[data.status] || 'text-secondary-emphasis bg-secondary-subtle'}`;
            statusBadge.textContent = statusTexts[data.status] || data.status;

            // Обновляем класс строки (подсветку)
            taskRow.classList.remove('table-active');
            if (data.status === 'copying' || data.status === 'verifying') {
                taskRow.classList.add('table-active');
            }
        }

        // 2. Обновляем прогресс-бар
        const progressBar = taskRow.querySelector('.progress-bar');
        if (progressBar) {
            if (data.status === 'completed') {
                // Задача завершена - показываем 100% зелёный
                progressBar.className = 'progress-bar bg-success';
                progressBar.style.width = '100%';
                progressBar.textContent = '100%';
            } else if (data.status === 'copying' || data.status === 'verifying' || data.status === 'pending') {
                // Активные задачи
                progressBar.className = 'progress-bar progress-bar-striped progress-bar-animated';
                const progress = Math.min(data.progress || 0, 100);
                progressBar.style.width = progress + '%';
                progressBar.textContent = Math.round(progress) + '%';
                progressBar.setAttribute('aria-valuenow', progress);
            } else {
                // Для completed и error - уже обработано выше
                if (data.status === 'error') {
                    // Ошибка - скрываем прогресс-бар
                    const progressContainer = taskRow.querySelector('.progress');
                    if (progressContainer) {
                        progressContainer.innerHTML = '<span class="text-muted">-</span>';
                    }
                }
            }
        } else if (data.status === 'copying' || data.status === 'verifying') {
            // Если прогресс-бара не было (статус был 'pending'), добавляем его
            const td = taskRow.querySelector('td:nth-child(4)'); // 4-я колонка - прогресс
            if (td) {
                td.innerHTML = `
                    <div class="progress" style="height: 20px;">
                        <div class="progress-bar progress-bar-striped progress-bar-animated"
                             role="progressbar"
                             style="width: ${Math.round(data.progress || 0)}%"
                             aria-valuenow="${Math.round(data.progress || 0)}"
                             aria-valuemin="0"
                             aria-valuemax="100">
                            ${Math.round(data.progress || 0)}%
                        </div>
                    </div>
                `;
            }
        }

        // 3. Обновляем скорость
        const speedCell = taskRow.querySelector('.speed-value');
        if (speedCell) {
            if (data.speed_mbps !== undefined && data.speed_mbps > 0) {
                speedCell.textContent = data.speed_mbps.toFixed(1) + ' MB/s';
                speedCell.querySelector('.text-muted')?.remove(); // Убираем плейсхолдер
            } else if (data.status === 'completed' || data.status === 'error') {
                speedCell.innerHTML = '<span class="text-muted">-</span>';
            }
        }

        // 4. Обновляем размер файла
        const sizeCell = taskRow.querySelector('.size-value');
        if (sizeCell && data.transferred_gb !== undefined && data.file_size_gb !== undefined) {
            sizeCell.textContent = data.transferred_gb.toFixed(2) + ' / ' + data.file_size_gb.toFixed(2) + ' GB';
        }

        // 5. Если задача завершилась или ошибка - обновляем дату завершения
        if (data.status === 'completed' || data.status === 'error') {
            const completedCell = taskRow.querySelector('td:nth-child(8)'); // 8-я колонка - время завершения
            if (completedCell) {
                const now = new Date();
                const formatted = now.getFullYear() + '-' +
                    String(now.getMonth() + 1).padStart(2, '0') + '-' +
                    String(now.getDate()).padStart(2, '0') + ' ' +
                    String(now.getHours()).padStart(2, '0') + ':' +
                    String(now.getMinutes()).padStart(2, '0') + ':' +
                    String(now.getSeconds()).padStart(2, '0');
                completedCell.textContent = formatted;
            }

            // Активируем кнопку "Повторить"
            const retryBtn = taskRow.querySelector('.retry-btn');
            if (retryBtn) {
                retryBtn.disabled = false;
            }
        }
    }

    loadFileManager(pageNumber = null) {
        if (!pageNumber) {
            const currentPage = document.querySelector('.pagination .page-item.active');
            pageNumber = currentPage?.dataset?.pageNumber || 1;
        }

        // Показываем спиннер
        this.container.innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border text-primary" style="width: 3rem; height: 3rem;" role="status">
                    <span class="visually-hidden">Загрузка данных...</span>
                </div>
                <p class="mt-3">Загрузка списка задач...</p>
            </div>
        `;

        fetch('/file-manager/load/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({
                search_input: this.searchInput?.value || '',
                page_number: pageNumber,
                status_filter: this.statusFilter?.value || null
            }),
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                this.container.innerHTML = data.html;
            } else {
                this.container.innerHTML = '<div class="alert alert-danger">Ошибка загрузки данных</div>';
                console.error('Error:', data.message);
            }
        })
        .catch(error => {
            console.error('Error loading file manager:', error);
            this.container.innerHTML = '<div class="alert alert-danger">Ошибка загрузки данных</div>';
        });
    }

    startPolling() {
        // Polling каждые 5 секунд для обновления активных задач
        setInterval(() => {
            this.pollActiveTasks();
        }, 5000);
    }

    pollActiveTasks() {
        // Проверяем, есть ли активные задачи на странице
        const activeTasks = document.querySelectorAll('.progress-bar-striped');
        if (activeTasks.length > 0) {
            // Перезагружаем только прогресс-бары
            this.loadFileManager();
        }
    }
}

function retryCopyTask(taskId) {
    if (!confirm('Вы уверены, что хотите повторить копирование?')) {
        return;
    }

    fetch('/file-manager/retry/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
            task_id: taskId
        }),
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // Показываем уведомление
            if (window.notificationManager) {
                window.notificationManager.showToast({
                    type: 'success',
                    message: data.message,
                    timestamp: new Date().toISOString()
                });
            }
            // Перезагружаем таблицу
            fileManager.loadFileManager();
        } else {
            console.error('Error:', data.message);
            if (window.notificationManager) {
                window.notificationManager.showToast({
                    type: 'error',
                    message: data.message,
                    timestamp: new Date().toISOString()
                });
            }
        }
    })
    .catch(error => {
        console.error('Error retrying task:', error);
    });
}

// function updateFileManagerButtonFromWS(activeCount, errorCount) {
//     const btn = document.getElementById('file_manager_btn');
//     if (!btn) return;
//
//     btn.classList.remove('active-tasks', 'error-tasks');
//
//     if (errorCount > 0) {
//         btn.classList.add('error-tasks');
//     } else if (activeCount > 0) {
//         btn.classList.add('active-tasks');
//     }
// }

function switchPageNumber(element) {
    const pageNumber = element.dataset?.pageNumber || 1;
    fileManager.loadFileManager(pageNumber);
}

// Инициализация при загрузке страницы
let fileManager;
document.addEventListener('DOMContentLoaded', function() {
    fileManager = new FileManager();
});

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}