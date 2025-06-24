function ValidateForm() {
    const form = document.querySelector('.needs-validation')
    const TaskReadyModal = bootstrap.Modal.getInstance(document.getElementById('TaskReady')) ||
                        new bootstrap.Modal(document.getElementById('TaskReady'));
    const CenzCommentModal = bootstrap.Modal.getInstance(document.getElementById('CenzComment')) ||
                        new bootstrap.Modal(document.getElementById('CenzComment'));
    if (form.checkValidity()) {
        TaskReadyModal.hide();
        CenzCommentModal.toggle();
    }
    else {
        form.classList.add('was-validated');
    }
};

window.addEventListener('load', function() {
    let seasons = document.getElementsByClassName('season');

    for (let i = 0; i < seasons.length; i++) {
        let season = seasons[i];
        let parentCheckbox = season.querySelector('input[type="checkbox"]');
        let episodes = season.getElementsByTagName('li');
        let episodeCheckboxes = [];

        // Все чекбоксы эпизодов
        for (let n = 0; n < episodes.length; n++) {
            let checkbox = episodes[n].querySelector('input[type="checkbox"]');
            if (checkbox) {
                episodeCheckboxes.push(checkbox);
                checkbox.addEventListener('change', updateParentCheckbox);
            }
        };
        parentCheckbox.addEventListener('change', function() {
            // При изменении родительского чекбокса обновляем все дочерние
            for (let checkbox of episodeCheckboxes) {
                checkbox.checked = this.checked;
            }
            // И вызываем обновление состояния
            updateParentCheckbox();
        });

        // Функция обновления состояния родительского чекбокса
        function updateParentCheckbox() {
            let checkedCount = episodeCheckboxes.filter(checkbox => checkbox.checked).length;
            let completeTask = season.querySelector('[name="complete_task"]');

            if (checkedCount > 0 && checkedCount < episodeCheckboxes.length) {
                parentCheckbox.indeterminate = true;
                parentCheckbox.checked = false;
                completeTask.style.display = 'inline';
            }
            else if (checkedCount === episodeCheckboxes.length) {
                parentCheckbox.indeterminate = false;
                parentCheckbox.checked = true;
                completeTask.style.display = 'inline';
            }
            else if (checkedCount === 0) {
                parentCheckbox.indeterminate = false;
                parentCheckbox.checked = false;
                completeTask.style.display = 'none';
            }
        };
    };
});

function ShowTaskReady(program_id) {
    let season = document.getElementById(program_id);
    let parentCheckbox = season.querySelector('input[type="checkbox"]');
    let episodes = season.getElementsByTagName('li');
    let episodeCheckboxes = [];
    for (let n = 0; n < episodes.length; n++) {
        let checkbox = episodes[n].querySelector('input[type="checkbox"]');
        if (checkbox && checkbox.checked) {
            episodeCheckboxes.push(checkbox.value);
            }
    };
    let taskReady = document.getElementById('task_ready');
    taskReady.value = Array.from(episodeCheckboxes);
    let cenzInfoChange = document.getElementById('cenz_info_change');
    cenzInfoChange.value = Array.from(episodeCheckboxes);
    let readyCenzInfo = document.getElementById('ready_cenz_info');
    let modalLabel = document.getElementById('TaskReadyLabel');
    const TaskReadyModal = new bootstrap.Modal(document.getElementById('TaskReady'));

    readyCenzInfo.innerHTML = ''
    TaskReadyModal.toggle();
        fetch(`/load_cenz_data/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
                'X-Requested-With': 'XMLHttpRequest'
            },

            body: JSON.stringify(episodeCheckboxes),
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(cenz_data => {
            console.log(cenz_data);
            if (cenz_data && cenz_data.html) {
                const fragment = document.createRange().createContextualFragment(cenz_data.html);
                readyCenzInfo.innerHTML = '';
                readyCenzInfo.appendChild(fragment);

            }
        })
        .catch(error => {
            modalLabel.textContent = `Ошибка загрузки данных`;
        });

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