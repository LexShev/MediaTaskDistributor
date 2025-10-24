const userId = document.body.dataset.userId || null;

// Вынесем функцию инициализации в отдельную функцию
function initializeNotifications() {
    const notificationsContainer = document.getElementById('notifications');
    if (notificationsContainer) {
        notificationsContainer.scrollTop = notificationsContainer.scrollHeight;
    }

    attachNotificationEvents();
}

// Функция для привязки обработчиков событий к уведомлениям
function attachNotificationEvents() {
    let notifications = Array.from(document.getElementsByClassName('notice-item'));
    notifications.forEach(function(elem) {
        // Удаляем старые обработчики, чтобы избежать дублирования
        elem.removeEventListener('mouseenter', handleNoticeMouseEnter);
        // Добавляем новый обработчик
        elem.addEventListener('mouseenter', handleNoticeMouseEnter);
    });
}

// Обработчик события mouseenter
function handleNoticeMouseEnter() {
    if (this.classList.contains('new-notice')) {
        const noticeId = this.dataset.noticeId;
        readNotice(noticeId);
        this.classList.remove('new-notice');
    }
}

window.addEventListener('DOMContentLoaded', function(){
    initializeNotifications();
});

function readNotice(noticeId) {
    fetch('/messenger/read_notice/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify([userId, noticeId]),
        credentials: 'same-origin'
        })
    .then(response => {
        if (!response.ok) {
             console.error(response.status);
        }
        return response.json();
    })
    .then(data => {
        if (data.status !== 'success') {
            console.error(data.message || 'Unknown server error');
        }
        updateUnreadNotifications(data.unread_notifications);
        updateTotalUnreadCount(data.total_unread);
    })
    .catch(error => {
        console.error('Error:', error);
    });
};

function updateUnreadNotifications(newCount) {
    const noticeBadge = document.getElementById('unread_notifications');
    if (!noticeBadge) return;

    if (newCount > 0) {
        noticeBadge.textContent = newCount;
        noticeBadge.style.display = '';
    }
    else {
        noticeBadge.style.display = 'none';
    }
};

function updateTotalUnreadCount(newCount) {
    const totalUnreadBadge = document.getElementById('total_unread_badge');
    if (!totalUnreadBadge) return;

    if (newCount > 0 && newCount <= 99) {
        totalUnreadBadge.textContent = newCount;
        totalUnreadBadge.style.display = '';
    }
    else if (newCount > 99) {
        totalUnreadBadge.textContent = '99+';
        totalUnreadBadge.style.display = '';
    }
    else {
        totalUnreadBadge.style.display = 'none';
    }
};

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
};

function loadEarlierNotifications(page) {
    const button = document.querySelector('.load-earlier-btn');
    const originalText = button.innerHTML;
    button.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Загрузка...';
    button.disabled = true;

    // Сохраняем текущую позицию скролла и высоту контейнера перед добавлением
    const messagesContainer = document.querySelector('#notification-messages');
    const scrollContainer = document.getElementById('notifications');
    const scrollTopBefore = scrollContainer.scrollTop;
    const scrollHeightBefore = scrollContainer.scrollHeight;

    fetch(`?page=${page}`)
        .then(response => response.text())
        .then(html => {
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = html;

            // Получаем новые сообщения и новую кнопку
            const newMessages = tempDiv.querySelector('#notification-messages').innerHTML;
            const newButtonContainer = tempDiv.querySelector('#load-earlier-container');

            // Добавляем новые сообщения в начало
            messagesContainer.innerHTML = newMessages + messagesContainer.innerHTML;

            // Перепривязываем обработчики событий к ВСЕМ уведомлениям
            attachNotificationEvents();

            // Обновляем кнопку из нового HTML
            if (newButtonContainer) {
                const buttonContainer = document.querySelector('#load-earlier-container');
                buttonContainer.innerHTML = newButtonContainer.innerHTML;

                // Обновляем обработчик события для новой кнопки
                const newButton = buttonContainer.querySelector('.load-earlier-btn');
                if (newButton) {
                    const newPage = newButton.getAttribute('onclick').match(/\d+/)[0];
                    newButton.setAttribute('onclick', `loadEarlierNotifications(${newPage})`);
                }
            } else {
                // Если больше нет страниц - удаляем кнопку
                const buttonContainer = document.querySelector('#load-earlier-container');
                if (buttonContainer) {
                    buttonContainer.remove();
                }
            }

            // Восстанавливаем позицию скролла, чтобы контент не "прыгал"
            // Добавляем разницу в высоте контента до и после загрузки
            const scrollHeightAfter = scrollContainer.scrollHeight;
            const heightDifference = scrollHeightAfter - scrollHeightBefore;
            scrollContainer.scrollTop = scrollTopBefore + heightDifference;

        })
        .catch(error => {
            console.error('Ошибка загрузки:', error);
            button.innerHTML = originalText;
            button.disabled = false;
        });
}