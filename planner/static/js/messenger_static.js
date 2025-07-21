const userId = document.body.dataset.userId || null;
const programId = document.getElementById('program_id').dataset.programId || null;

window.addEventListener('DOMContentLoaded', function(){
    const messagesContainer = document.getElementById('messages');
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    let inputMessage = document.getElementById('id_message')
    inputMessage.focus()
});

window.addEventListener('load', function(){
    let messages = Array.from(document.getElementsByClassName('message-item'));
    messages.forEach(function(elem) {
        elem.addEventListener('mouseenter', function() {
            if (elem.classList.contains('new-message')) {
                const messageId = elem.dataset.messageId;
                readMessage(messageId);
                elem.classList.remove('new-message');
            }
        })
    })
});

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


let inputMessage = document.getElementById('id_message')
let sendMessageBtn = document.getElementById('send_message')
let messageForm = document.getElementById('message_form')
inputMessage.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault(); // Предотвращаем перенос строки
        messageForm.submit(); // Отправляем форму
    }
});

function sendMessage() {

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
    $.ajax({
        url: `/messenger/${programId}/`,
        type: "get",
        success: function(data) {
            let newDoc = new DOMParser().parseFromString(data, 'text/html');
            let newMessages = newDoc.querySelector('.messages').innerHTML;
            document.querySelector('.messages').innerHTML = newMessages;
        }
    });
}

//setInterval(updateMessages, 5000);

document.getElementById('id_file_path').addEventListener('change', function(e) {
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

    const messages = document.getElementById('messages');
    messages.appendChild(preview);
});

function enlargeImage(img) {
    document.getElementById('modalImage').src = img.src;
    document.getElementById('imageModalLabel').textContent = img.alt || "Изображение";
}