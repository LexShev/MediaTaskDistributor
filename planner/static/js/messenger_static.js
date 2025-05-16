window.addEventListener('load', function(){
    let inputMessage = document.getElementById('id_message')
    inputMessage.focus()
});

window.addEventListener('load', function(){
    let messages = Array.from(document.getElementsByClassName('message-item'))
    messages.forEach(function(elem) {
        elem.addEventListener('mouseenter', function() {
        elem.classList.remove('new-message');
        })
    })
});

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

function updateMessages() {
    $.ajax({
        url: "{% url 'home' %}messenger/{{ program_id }}",
        type: "get",
        success: function(data) {
            let newDoc = new DOMParser().parseFromString(data, 'text/html');
            let newMessages = newDoc.querySelector('.messages').innerHTML;
            document.querySelector('.messages').innerHTML = newMessages;
        }
    });
}

<!--    setInterval(updateMessages, 5000);-->

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