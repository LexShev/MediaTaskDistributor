window.addEventListener('DOMContentLoaded', function() {
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

function toggleSeason(seasonId) {
    const episodesContainer = document.getElementById(`episodes-${seasonId}`);
    const toggleIcon = document.getElementById(`toggle-${seasonId}`);

    // Проверка на существование элементов
    if (!episodesContainer || !toggleIcon) {
        console.warn(`Элементы для сезона ${seasonId} не найдены`);
        return;
    }

    if (episodesContainer.classList.contains('collapsed')) {
        episodesContainer.classList.remove('collapsed');
        episodesContainer.classList.add('expanded');
        toggleIcon.style.transform = 'rotate(0deg)';
        localStorage.setItem(`season-${seasonId}`, 'expanded');
    } else {
        episodesContainer.classList.remove('expanded');
        episodesContainer.classList.add('collapsed');
        toggleIcon.style.transform = 'rotate(-90deg)';
        localStorage.setItem(`season-${seasonId}`, 'collapsed');
    }
}

// Восстановление состояния при загрузке
document.addEventListener('DOMContentLoaded', function() {
    const seasonContainers = document.querySelectorAll('.episodes-container');
    if (!seasonContainers || seasonContainers.length === 0) {
        return;
    }
    seasonContainers.forEach(container => {
        const seasonId = container.id.replace('episodes-', '');
        const savedState = localStorage.getItem(`season-${seasonId}`);

        if (savedState === 'expanded') {
            container.classList.add('expanded');
            document.getElementById(`toggle-${seasonId}`).style.transform = 'rotate(0deg)';
        } else {
            container.classList.add('collapsed');
            document.getElementById(`toggle-${seasonId}`).style.transform = 'rotate(-90deg)';


        }
    });
});

function initializeDropZones() {
    // Находим все контейнеры с файлами
    const cenzContainers = document.querySelectorAll('.cenz_container');

    cenzContainers.forEach(container => {
        const dropZone = container.querySelector('.drop-zone');
        const fileInput = container.querySelector('input[type="file"]');

        if (!dropZone || !fileInput) return;

        // Функции для предотвращения стандартного поведения
        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        function highlight() {
            dropZone.classList.add('dragover');
            fileInput.classList.add('dragover');
        }

        function unhighlight() {
            dropZone.classList.remove('dragover');
            fileInput.classList.remove('dragover');
        }

        // Обработчики событий перетаскивания
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, preventDefaults, false);
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, highlight, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, unhighlight, false);
        });

        // Обработка drop - файл перетащили в зону
        dropZone.addEventListener('drop', handleDrop, false);

        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;

            if (files.length > 0) {
              //  Берем только ПЕРВЫЙ файл, даже если перетащили несколько
              const firstFile = files[0];

            // Создаем новый FileList с одним файлом
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(firstFile);

            // Присваиваем только первый файл в input
            fileInput.files = dataTransfer.files;

            // Триггерим событие change, чтобы другие обработчики узнали о выборе файла
            const event = new Event('change', { bubbles: true });
            fileInput.dispatchEvent(event);

            // Меняем стиль drop-zone чтобы показать, что файл выбран
            updateDropZoneAppearance(dropZone, firstFile.name);

            }
        }

        // Клик по зоне тоже открывает выбор файла
        dropZone.addEventListener('click', function(e) {
            // Кликаем только если кликнули не по самому input
            if (e.target !== fileInput) {
              fileInput.click();
            }
        });

        // Обработчик изменения файла через стандартный диалог
        fileInput.addEventListener('change', function() {

            if (this.files.length > 0) {
                const fileName = this.files[0].name;
                updateDropZoneAppearance(dropZone, fileName);
            } else {
              // Если файл сброшен
                resetDropZoneAppearance(dropZone);
            }
        });

        function updateDropZoneAppearance(dropZone, fileName) {
            dropZone.classList.remove('border-secondary', 'text-secondary');
            dropZone.classList.add('file-selected', 'border-success', 'text-success');
            fileInput.classList.remove('border-secondary', 'text-secondary');
            fileInput.classList.add('border-success', 'text-success');

            const paragraphs = dropZone.querySelectorAll('p');
            if (paragraphs.length >= 2) {
                paragraphs[0].textContent = `Выбран файл: ${fileName}`;
                paragraphs[1].textContent = ''; // Очищаем второй параграф
            } else if (paragraphs.length === 1) {
                paragraphs[0].textContent = `Выбран файл: ${fileName}`;
            }
        };

        function resetDropZoneAppearance(dropZone) {
            dropZone.classList.remove('file-selected', 'border-success', 'text-success');
            dropZone.classList.add('border-secondary', 'text-secondary');
            fileInput.classList.remove('border-success', 'text-success');
            fileInput.classList.add('border-secondary', 'text-secondary');

            const paragraphs = dropZone.querySelectorAll('p');
            if (paragraphs.length >= 2) {
                paragraphs[0].textContent = 'Перетащите файл сюда...';
                paragraphs[1].textContent = '(или кликните для выбора)';
            }
        };



    });
};

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
        CenzApproveBatch();
    };

};

function showReadyListModal() {
    let cenzList = document.getElementById('cenz_ready_list');
    cenzList.innerHTML = '';
    let programDataList = JSON.parse(document.getElementById('program_data_list').dataset.cenzMaterials) || [];
    programDataList.forEach(programData => {
        let [program_id, old_file_name, old_file_path] = programData;

        let cenzContainer = document.createElement("div");
        cenzContainer.id = `cenz_container_${program_id}`;
        cenzContainer.dataset.programId = program_id;
        cenzContainer.classList.add('cenz_container');

        let cenz_program_id = document.createElement("input");
        cenz_program_id.type = 'hidden';
        cenz_program_id.name = 'cenz_program_id';
        cenz_program_id.value = program_id;
        cenzContainer.appendChild(cenz_program_id);

        let file_name = document.createElement("h5");
        file_name.classList.add('file_name', 'my-4');
        file_name.textContent = old_file_name;
        cenzContainer.appendChild(file_name);

        let file_path_header = document.createElement("h6");
        file_path_header.textContent = 'Укажите путь к готовому файлу';
        cenzContainer.appendChild(file_path_header);

        let switchContainer = document.createElement('div');
        switchContainer.classList.add('form-check');
        switchContainer.classList.add('form-switch');
        switchContainer.classList.add('my-2');
        cenzContainer.appendChild(switchContainer);

        let switcher = document.createElement("input");
        switcher.classList.add('form-check-input');
        switcher.type = 'checkbox';
        switcher.role = 'switch';
        switcher.id = `switcher_${program_id}`;
        switcher.name = 'switcher';
        switcher.setAttribute('onclick', `checkNoCenz(cenz_container_${program_id})`)
        switchContainer.appendChild(switcher);

        let switchLabel = document.createElement("label");
        switchLabel.classList.add('form-check-label');
        switchLabel.textContent = 'CENZ не требуется';
        switchLabel.setAttribute('for', `switcher_${program_id}`);
        switchContainer.appendChild(switchLabel);

        let drop_zone = document.createElement("div");
        drop_zone.classList.add('drop-zone', 'border-secondary', 'text-center', 'text-secondary', 'p-2', 'my-2');
        cenzContainer.appendChild(drop_zone);

        let drop_zone_text_1 = document.createElement("p");
        drop_zone_text_1.textContent = 'Перетащите файл сюда...';
        drop_zone_text_1.classList.add('my-2');
        drop_zone.appendChild(drop_zone_text_1);
        let drop_zone_text_2 = document.createElement("p");
        drop_zone_text_2.textContent = '(или кликните для выбора)';
        drop_zone_text_2.classList.add('my-2');
        drop_zone.appendChild(drop_zone_text_2);

        let cenz_file_path_group = document.createElement("div");
        cenz_file_path_group.classList.add('input-group', 'file-input-group', 'my-2');
        cenzContainer.appendChild(cenz_file_path_group);

        let cenz_file_path = document.createElement("input");
        cenz_file_path.classList.add('form-control', 'rounded');
        cenz_file_path.setAttribute('accept', 'video/*');
        cenz_file_path.setAttribute('type', 'file');
        cenz_file_path.name = 'cenz_file_path';
        cenz_file_path.id = `cenz_file_path_${program_id}`;
        cenz_file_path_group.appendChild(cenz_file_path);

        let invalid_feedback = document.createElement("div");
        invalid_feedback.classList.add('invalid-feedback');
        invalid_feedback.textContent = 'Необходимо указать файл'
        cenz_file_path_group.appendChild(invalid_feedback);

        let cenz_header = document.createElement("h6");
        cenz_header.textContent = 'Комментарий к материалу';
        cenzContainer.appendChild(cenz_header);

        let cenz_comment = document.createElement("textarea");
        cenz_comment.classList.add('form-control');
        cenz_comment.classList.add('my-2');
        cenz_comment.name = 'cenz_comment';
        cenz_comment.style = 'min-height: 60px';
        cenzContainer.appendChild(cenz_comment);

        let divider = document.createElement("hr");
        divider.style = 'width: 40%; size: 2;';
        divider.classList.add('my-4');
        cenzContainer.appendChild(divider);

        cenzList.appendChild(cenzContainer);
    });
    const TaskReadyModal = bootstrap.Modal.getInstance(document.getElementById('TaskReady')) ||
                        new bootstrap.Modal(document.getElementById('TaskReady'));
    if (programDataList.length > 0) {
        const readyListModal = bootstrap.Modal.getInstance(document.getElementById('readyListModal')) ||
                            new bootstrap.Modal(document.getElementById('readyListModal'));

        document.activeElement.blur();
        TaskReadyModal.hide();
        readyListModal.toggle();

        initializeDropZones();
    }
    else {
        console.log('error');
        errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
        document.activeElement.blur();
        TaskReadyModal.hide();
        errorModal.toggle();
    }

};

function checkNoCenz(container) {
    let noCenz = container.querySelector("input[name='switcher']").checked;
    const dropZone = container.querySelector(".drop-zone");
    const fileInputGroup = container.querySelector(".file-input-group");
    let cenz_file_path = container.querySelector("input[name='cenz_file_path']");
    cenz_file_path.classList.remove('is-invalid', 'is-valid');

    const event = new Event('change', { bubbles: true });
    cenz_file_path.dispatchEvent(event);
    cenz_file_path.value = ''

    if (noCenz) {
        dropZone.style.display = 'none';
        fileInputGroup.style.display = 'none';
    }
    else {
        dropZone.style.display = '';
        fileInputGroup.style.display = '';
    };
};

function ValidateFileUpload(task) {
    let cenzContainers = document.querySelectorAll('.cenz_container');
    let allValid = true;

    cenzContainers.forEach(container => {
        let noCenz = container.querySelector("input[name='switcher']");
        let cenz_file_path = container.querySelector("input[name='cenz_file_path']");

        // Сбрасываем стили
        cenz_file_path.classList.remove('is-invalid', 'is-valid');

        // Проверяем условия
        if (!noCenz.checked && cenz_file_path.files.length < 1) {
            cenz_file_path.classList.add('is-invalid');
            allValid = false;
        } else {
            cenz_file_path.classList.add('is-valid');
        }
    });

    // Если все валидны - отправляем данные
    if (allValid) {
        CenzReadyBatch();
    } else {
        console.log('Есть ошибки валидации - проверьте выделенные поля');
    }

};

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

function CenzApproveBatch() {
    let cenzData = [];
    let forms = {}
    
    let programIdList = JSON.parse(document.getElementById('program_data_list').dataset.programIdList);
    const cenzFormElements = document.getElementById('cenz_form').elements;
    Array.from(cenzFormElements).forEach(element => {
        if (element.name) {
            forms[element.name] = element.value;
        };
    });
    cenzData.push(programIdList, forms);
    sendData('cenz_info_change_batch', cenzData)
};

function CenzReadyBatch() {
    let fileInfo = []
    let forms = {}

    let programIdList = JSON.parse(document.getElementById('program_data_list').dataset.programIdList);
    const cenzFormElements = document.getElementById('cenz_form').elements;
    Array.from(cenzFormElements).forEach(element => {
        if (element.name) {
            forms[element.name] = element.value;
        };
    });

    let cenzContainers = document.querySelectorAll('.cenz_container');
    cenzContainers.forEach(container => {
        let noCenz = container.querySelector("input[name='switcher'");
        let program_id = container.dataset.programId;
        let cenz_comment = container.querySelector("textarea[name='cenz_comment']");
        let file_name = container.querySelector(".file_name");
        let cenz_file_path = container.querySelector("input[name='cenz_file_path']");
        fileInfo.push([
            noCenz?.checked || '',
            program_id || '',
            cenz_comment?.value || '',
            file_name?.textContent || '',
            cenz_file_path?.files?.[0]?.name || ''
        ])
    });
    sendData('task_ready_batch', [forms, fileInfo]);
};

function updateMainSwitcher() {
    let mainSwitcher = document.querySelector("input[name='main_switcher'");
    let readyListContainer = document.getElementById("cenz_ready_list_container");
    let cenzContainers = document.querySelectorAll('.cenz_container');

    const isChecked = mainSwitcher.checked;

    cenzContainers.forEach(container => {
        // Устанавливаем свойство checked
        const programId = container.dataset.programId

        const switcher = container.querySelector("input[name='switcher'");
        switcher.checked = isChecked;
        checkNoCenz(container);

    });
};

function sendData(task, cenzData) {
    fetch(`/${task}/`, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'),
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
            document.activeElement.blur();
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