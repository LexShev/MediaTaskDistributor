const userId = document.body.dataset.userId || null;
const programId = document.querySelector('[data-program-id]')?.dataset.programId || null;

window.addEventListener('DOMContentLoaded', function(){
    const messagesContainer = document.getElementById('messages-content') || document.getElementById('messages');
    if (messagesContainer) {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    let inputMessage = document.getElementById('id_message');
    if (inputMessage) {
        inputMessage.focus();
    }
});

window.addEventListener('load', function(){
    initMessageHandlers();
});

function initMessageHandlers() {
    let messages = Array.from(document.querySelectorAll('.message-item'));
    messages.forEach(function(elem) {
        // Убираем старые обработчики чтобы избежать дублирования
        elem.removeEventListener('mouseenter', handleMessageHover);
        // Добавляем новые
        elem.addEventListener('mouseenter', handleMessageHover);
    });
}

function handleMessageHover() {
    if (this.classList.contains('new-message')) {
        const messageId = this.dataset.messageId;
        readMessage(messageId);
        this.classList.remove('new-message');
    }
}

function readMessage(messageId) {
    fetch('/messenger/read_message/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify([userId, messageId, programId]),
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
        console.log(data);
        updateUnreadCount(data.cur_unread);
        updateTotalUnreadCount(data.total_unread);
    })
    .catch(error => {
        console.error('Error:', error);
    });
};

function updateUnreadCount(newCount) {
    const chatItem = document.querySelector(`li[data-program-id="${programId}"]`);
    if (!chatItem) return;
    const badge = chatItem.querySelector('.unread-badge');
    if (badge && newCount > 0) {
        badge.textContent = newCount;
        badge.style.display = '';
    }
    else if (badge) {
        badge.style.display = 'none';
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


let inputMessage = document.getElementById('id_message');
let sendMessageBtn = document.getElementById('send_message');
let messageForm = document.getElementById('message_form');

if (inputMessage && messageForm) {
    inputMessage.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            messageForm.submit();
        }
    });

    inputMessage.addEventListener('keyup', function(e) {
        if (e.key === '@') {
            findMention();
        }
    });
}

function modifyMessage(element) {
    inputMessage.value = inputMessage.value + element.dataset.plannerWorkerId;
};

function findMention() {
    const mentionDropdown = document.getElementById('mentionDropdown');
    const dropdown = new bootstrap.Dropdown(mentionDropdown);
    dropdown.show();
};

function sendNotice() {
    let notice = {'sender': sender, 'recipient': recipient, 'program_id': program_id, 'message': message};
    fetch('/messenger/send_notice/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify(notice),
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
        console.log(data);
    })
    .catch(error => {
        console.error('Error:', error);
    });
};

function updateMessages() {
    if (!programId) return;

    $.ajax({
        url: `/messenger/${programId}/`,
        type: "get",
        success: function(data) {
            let newDoc = new DOMParser().parseFromString(data, 'text/html');
            let newMessagesContent = newDoc.querySelector('#messages-content')?.innerHTML;
            let messagesContainer = newDoc.querySelector('.messages')?.innerHTML;

            if (newMessagesContent) {
                document.querySelector('#messages-content').innerHTML = newMessagesContent;
            } else if (messagesContainer) {
                document.querySelector('.messages').innerHTML = messagesContainer;
            }

            // Переинициализируем обработчики
            initMessageHandlers();
            initMediaHandlers();
        }
    });
}

//setInterval(updateMessages, 5000);

const fileInput = document.getElementById('id_file_path');
if (fileInput) {
    fileInput.addEventListener('change', function(e) {
        const file_path = e.target.files[0];
        if (!file_path) return;

        const preview = document.createElement('div');
        preview.className = 'file-preview';

        if (file_path.type.startsWith('image/')) {
            const img = document.createElement('img');
            img.src = URL.createObjectURL(file_path);
            img.style.maxWidth = '100px';
            preview.appendChild(img);
        } else {
            preview.textContent = `Файл: ${file_path.name}`;
        }

        const messagesContent = document.getElementById('messages-content') || document.getElementById('messages');
        if (messagesContent) {
            messagesContent.appendChild(preview);
        }
    });
}

function enlargeImage(img) {
    const modalImage = document.getElementById('modalImage');
    const modalLabel = document.getElementById('imageModalLabel');

    if (modalImage && img) {
        modalImage.src = img.src;
    }
    if (modalLabel && img) {
        modalLabel.textContent = img.alt || "Изображение";
    }
}

function loadEarlierMessages(programId, page) {
    const button = document.querySelector('.load-earlier-messages-btn');
    if (!button) return; // Защита от отсутствия кнопки

    const originalText = button.innerHTML;
    button.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Загрузка...';
    button.disabled = true;

    fetch(`/messenger/${programId}/?page=${page}`)
        .then(response => response.text())
        .then(html => {
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = html;

            // Безопасное получение элементов
            const newMessagesContent = tempDiv.querySelector('#messages-content');
            const newButtonContainer = tempDiv.querySelector('#load-earlier-messages-container');

            if (!newMessagesContent) {
                throw new Error('Не найден контейнер сообщений');
            }

            // Добавляем новые сообщения в начало
            const messagesContent = document.querySelector('#messages-content');
            if (messagesContent) {
                messagesContent.innerHTML = newMessagesContent.innerHTML + messagesContent.innerHTML;
            }

            // Обновляем кнопку
            const currentButtonContainer = document.querySelector('#load-earlier-messages-container');
            if (newButtonContainer && currentButtonContainer) {
                currentButtonContainer.innerHTML = newButtonContainer.innerHTML;

                const newButton = currentButtonContainer.querySelector('.load-earlier-messages-btn');
                if (newButton) {
                    const onclickAttr = newButton.getAttribute('onclick');
                    const matches = onclickAttr.match(/\d+/g);
                    if (matches && matches.length >= 2) {
                        const newPage = matches[1];
                        newButton.setAttribute('onclick', `loadEarlierMessages(${programId}, ${newPage})`);
                    }
                }
            } else if (currentButtonContainer) {
                // Удаляем кнопку, если больше нет страниц
                currentButtonContainer.remove();
            }

            // Переинициализируем обработчики
            initMediaHandlers();

            // Прокручиваем к началу
            window.scrollTo({ top: 0, behavior: 'smooth' });
        })
        .catch(error => {
            console.error('Ошибка загрузки сообщений:', error);
            button.innerHTML = originalText;
            button.disabled = false;
        });
}

function initMediaHandlers() {
    // Обработчики для изображений
    document.querySelectorAll('.chat-image').forEach(img => {
        img.onclick = function() { enlargeImage(this); };
    });

    // Инициализация Bootstrap модальных окон
    document.querySelectorAll('[data-bs-toggle="modal"]').forEach(element => {
        element.setAttribute('data-bs-target', '#imageModal');
    });
}