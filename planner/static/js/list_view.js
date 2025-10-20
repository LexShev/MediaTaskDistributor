function ValidateForm(task) {
    let workDate = document.getElementById('work_date_form')
    let cenzRate = document.getElementById('cenz_rate_form')
    let engineers = document.getElementById('engineers_form')

    if (!workDate.value || !cenzRate.value || !engineers.value) {
        workDate.classList.add('is-invalid');
        cenzRate.classList.add('is-invalid');
        engineers.classList.add('is-invalid');
        return;
        }
    workDate.classList.remove('is-invalid');
    cenzRate.classList.remove('is-invalid');
    engineers.classList.remove('is-invalid');

    if (task === 'task_ready_batch') {
        showReadyListModal();
    }
    else if (task === 'cenz_info_change_batch') {
        CenzApproveBatch(task);
    };

};

function showReadyListModal() {
    let cenzList = document.getElementById('cenz_ready_list');
    cenzList.innerHTML = '';
    let programDataList = JSON.parse(document.getElementById('program_data_list').dataset.cenzMaterials) || [];
    programDataList.forEach(programData => {
        let cenzContainer = document.createElement("div");
        cenzContainer.classList.add('cenz_container')

        let [program_id, old_file_name, old_file_path] = programData;

        let switchContainer = document.createElement('div');
        switchContainer.classList.add('form-check');
        switchContainer.classList.add('form-switch');
        cenzContainer.appendChild(switchContainer);

        let switcher = document.createElement("input");
        switcher.classList.add('form-check-input');
        switcher.type = 'checkbox';
        switcher.role = 'switch';
        switcher.id = `switcher_${program_id}`;
        switcher.name = 'switcher';
        switchContainer.appendChild(switcher);

        let switchLabel = document.createElement("label");
        switchLabel.classList.add('form-check-label');
        switchLabel.textContent = 'CENZ не требуется';
        switchLabel.setAttribute('for', `switcher_${program_id}`);
        switchContainer.appendChild(switchLabel);

        let cenz_program_id = document.createElement("input");
        cenz_program_id.type = 'hidden';
        cenz_program_id.name = 'cenz_program_id';
        cenz_program_id.value = program_id;
        cenzContainer.appendChild(cenz_program_id);

        let file_name = document.createElement("h5");
        file_name.classList.add('my-2');
        file_name.textContent = old_file_name;
        file_name.name = 'file_name'
        cenzContainer.appendChild(file_name);

        let cenz_header = document.createElement("h6");
        cenz_header.textContent = 'Комментарий к материалу';
        cenzContainer.appendChild(cenz_header);

        let cenz_comment = document.createElement("textarea");
        cenz_comment.classList.add('form-control');
        cenz_comment.classList.add('my-2');
        cenz_comment.name = 'cenz_comment';
        cenz_comment.style = 'min-height: 50px';
        cenzContainer.appendChild(cenz_comment);

        let file_path_header = document.createElement("h6");
        file_path_header.textContent = 'Новый путь к файлу';
        cenzContainer.appendChild(file_path_header);

        let cenz_file_path_group = document.createElement("div");
        cenz_file_path_group.classList.add('input-group');
        cenzContainer.appendChild(cenz_file_path_group);

        let cenz_file_path = document.createElement("input");
        cenz_file_path.classList.add('form-control');
        cenz_file_path.setAttribute('accept', 'video/*');
        cenz_file_path.setAttribute('type', 'file');
        cenz_file_path.name = 'cenz_file_path';
        cenz_file_path.id = `cenz_file_path_${program_id}`;
        cenz_file_path_group.appendChild(cenz_file_path);

        let divider = document.createElement("hr");
        divider.style = 'width: 40%; size: 2;';
        cenzContainer.appendChild(divider);

        cenzList.appendChild(cenzContainer);
    });
    const TaskReadyModal = bootstrap.Modal.getInstance(document.getElementById('TaskReady')) ||
                        new bootstrap.Modal(document.getElementById('TaskReady'));
    console.log(programDataList, programDataList.length);
    if (programDataList.length > 0) {
        const readyListModal = bootstrap.Modal.getInstance(document.getElementById('readyListModal')) ||
                            new bootstrap.Modal(document.getElementById('readyListModal'));

        TaskReadyModal.hide();
        readyListModal.toggle();
    }
    else {
        console.log('error');
        errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
        TaskReadyModal.hide();
        errorModal.toggle();
    }

};

window.addEventListener('load', function() {
    let seasons = document.getElementsByClassName('season');

    for (let i = 0; i < seasons.length; i++) {
        let season = seasons[i];
        let parentCheckbox = season.querySelector('input[type="checkbox"]');
        let episodes = season.querySelectorAll('.episode');
        let programIdListChecked = [];

        // Все чекбоксы эпизодов
        for (let n = 0; n < episodes.length; n++) {
            let checkbox = episodes[n].querySelector('input[type="checkbox"]');
            if (checkbox) {
                programIdListChecked.push(checkbox);
                checkbox.addEventListener('change', updateParentCheckbox);
            }
        };
        parentCheckbox.addEventListener('change', function() {
            // При изменении родительского чекбокса обновляем все дочерние
            for (let checkbox of programIdListChecked) {
                checkbox.checked = this.checked;
            }
            // И вызываем обновление состояния
            updateParentCheckbox();
        });

        // Функция обновления состояния родительского чекбокса
        function updateParentCheckbox() {
            let checkedCount = programIdListChecked.filter(checkbox => checkbox.checked).length;
            let completeTask = season.querySelector('[name="complete_task"]');

            if (checkedCount > 0 && checkedCount < programIdListChecked.length) {
                parentCheckbox.indeterminate = true;
                parentCheckbox.checked = false;
                completeTask.style.display = 'inline';
            }
            else if (checkedCount === programIdListChecked.length) {
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
    let episodes = season.querySelectorAll('.episode');
    let programIdListChecked = [];
    let cenzMaterials = [];
    for (let n = 0; n < episodes.length; n++) {
        let checkbox = episodes[n].querySelector('input[type="checkbox"]');
        if (checkbox && checkbox.checked) {
            programIdListChecked.push(checkbox.value);
            cenzMaterials.push([checkbox.value || '',
            checkbox.dataset.fileName || '',
            checkbox.dataset.filePath || ''
            ]);
        }
    };
    let programDataList = document.getElementById('program_data_list');
    programDataList.dataset.programIdList = JSON.stringify(programIdListChecked);
    programDataList.dataset.cenzMaterials = JSON.stringify(cenzMaterials);

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

            body: JSON.stringify(programIdListChecked),
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(cenz_data => {
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

function checkNoCenz() {
    let noCenz = document.getElementById('no_cenz').checked
    let cenzCommentTitle = document.getElementById('cenz_comment_title')
    let cenzComment = document.getElementById('cenz_comment')
    let noCenzLabel = document.getElementById('no_cenz_label')
    if (noCenz) {
        noCenzLabel.classList.remove('text-secondary');
        cenzCommentTitle.classList.add('text-secondary');
        cenzComment.disabled = true;
    }
    else {
        noCenzLabel.classList.add('text-secondary');
        cenzCommentTitle.classList.remove('text-secondary');
        cenzComment.disabled = false;
    };
};

function CenzApproveBatch(task) {
    let cenzData = [];
    let forms = {}
    
    if (task === 'cenz_info_change_batch') {
        let programIdList = JSON.parse(document.getElementById('program_data_list').dataset.programIdList);
        const cenzFormElements = document.getElementById('cenz_form').elements;
        Array.from(cenzFormElements).forEach(element => {
            if (element.name) {
                forms[element.name] = element.value;
            };
        });
        cenzData.push(programIdList, forms)
    }
    else if (task === 'task_ready_batch') {
        let cenzContainers = document.querySelectorAll('.cenz_container');
        cenzContainers.forEach(container => {
            let noCenz = container.querySelector("input[name='no_cenz'");
            let program_id = container.querySelector("input[name='cenz_program_id']");
            let cenz_comment = container.querySelector("textarea[name='cenz_comment']");
            let file_name = container.querySelector("h5[name='file_name']");
            let cenz_file_path = container.querySelector("input[name='cenz_file_path']");
            cenzData.push([
                noCenz?.checked || '',
                program_id?.value || '',
                cenz_comment?.value || '',
                file_name?.textContent || '',
                cenz_file_path?.value || ''
            ])
        });
    };
    
    fetch(`/${task}/`, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': forms['csrfmiddlewaretoken'],
        'X-Requested-With': 'XMLHttpRequest'
    },
    body: JSON.stringify(cenzData),
    credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            window.location.href = `/list/`;
        }
        else {
            console.log('error', data.message)

            const CenzComment = bootstrap.Modal.getInstance(document.getElementById('CenzComment')) ||
                        new bootstrap.Modal(document.getElementById('CenzComment'));
            const errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
            error_message = document.getElementById('error_message');
            error_message.textContent = data.message;

            CenzComment.hide();
            errorModal.toggle();
        }
    })
    .catch(error => {
        console.error('Error sending info:', error);
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