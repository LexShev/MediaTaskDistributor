document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('search_input').value || '';
    fetch(`/on-air-report/load_on_air_task_table/?search_input=${encodeURIComponent(searchInput)}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            document.getElementById('on_air_task_table').innerHTML = data.html;
            updateMainProgramId();
            fastSearch();
        })
        .catch(error => {
            document.getElementById('on_air_task_table').innerHTML = `
                <div class="alert alert-danger">Ошибка загрузки данных</div>
            `;
            console.error(error);
    });
});

document.addEventListener('DOMContentLoaded', function() {
  const searchInput = document.getElementById('search_input');
  const dropdownMenu = document.getElementById('on_air_search_filter');

  if (searchInput && dropdownMenu) {
    // Создаем кастомное управление dropdown
    searchInput.addEventListener('focus', function() {
      dropdownMenu.classList.add('show');
    });
    // Скрываем при начале ввода
    searchInput.addEventListener('input', function() {
      if (this.value.length > 0) {
        setTimeout(() => {
            dropdownMenu.classList.remove('show');
        }, 300);
      }
    });

    // Закрываем при клике вне области
    document.addEventListener('click', function(event) {
      if (!event.target.closest('.dropdown')) {
        dropdownMenu.classList.remove('show');
      }
    });

    // Предотвращаем закрытие при клике внутри меню
    dropdownMenu.addEventListener('click', function(event) {
      event.stopPropagation();
    });
  }
});

window.addEventListener('DOMContentLoaded', function() {
    let fullSelectCheckbox = document.getElementById('full_select');
    let program_id_list = document.getElementsByName('program_id_check');
    program_id_list.forEach(function(program_id) {
        program_id.addEventListener('change', changeFullSelect);
    });

    function changeFullSelect() {
        let checked_list = [];
        for (let i = 0; i < program_id_list.length; i++) {
            if (program_id_list[i].checked) {
                checked_list.push(program_id_list[i]);
            }
        };
        if (0 < checked_list.length && checked_list.length < program_id_list.length) {
            fullSelectCheckbox.indeterminate = true;
            fullSelectCheckbox.checked = false;
        }
        else if (checked_list.length == program_id_list.length) {
            fullSelectCheckbox.indeterminate = false;
            fullSelectCheckbox.checked = true;
        }
        else if (checked_list.length == 0) {
            fullSelectCheckbox.indeterminate = false;
            fullSelectCheckbox.checked = false;
        }
    };
});

function changeProgramIdCheckbox() {
    let fullSelectCheckbox = document.getElementById('full_select');
    let tableBody = document.getElementById('tableBody');
    let visibleCheckboxes = tableBody.querySelectorAll('tr:not([style*="display: none"]) input[name="program_id_check"]:not(:disabled)');
    let checkedVisibleList = [];
        visibleCheckboxes.forEach(checkbox => {
        if (checkbox.checked) {
            checkedVisibleList.push(checkbox);
        }
    });

    if (checkedVisibleList.length > 0) {
        // Если есть выделенные видимые чекбоксы - снимаем выделение
        fullSelectCheckbox.indeterminate = false;
        fullSelectCheckbox.checked = false;
        visibleCheckboxes.forEach(checkbox => {
            checkbox.checked = false;
        });
    } else {
        // Если нет выделенных видимых чекбоксов - выделяем все видимые
        fullSelectCheckbox.indeterminate = false;
        fullSelectCheckbox.checked = true;
        visibleCheckboxes.forEach(checkbox => {
            checkbox.checked = true;
        });
    }
    updateSelectionCount();
};

function updateSelectionCount() {
    let program_id_check_list = document.getElementsByName('program_id_check');
    let checked_list = [];
    let duration = 0;

    for (let i = 0; i < program_id_check_list.length; i++) {
        if (program_id_check_list[i].checked) {
            checked_list.push(program_id_check_list[i].value);
            duration += parseFloat(program_id_check_list[i].dataset.duration);
        }
    }

    countMaterials(checked_list.length, duration);
    updateFullSelectCheckboxState(checked_list.length, program_id_check_list.length);
}

// Функция для обновления состояния главного чекбокса
function updateFullSelectCheckboxState(checkedCount, totalCount) {
    let fullSelectCheckbox = document.getElementById('full_select');

    if (0 < checkedCount && checkedCount < totalCount) {
        fullSelectCheckbox.indeterminate = true;
        fullSelectCheckbox.checked = false;
    }
    else if (checkedCount == totalCount) {
        fullSelectCheckbox.indeterminate = false;
        fullSelectCheckbox.checked = true;
    }
    else if (checkedCount == 0) {
        fullSelectCheckbox.indeterminate = false;
        fullSelectCheckbox.checked = false;
    }
};

function updateMainProgramId() {
    let program_id_check_list = document.getElementsByName('program_id_check');
    program_id_check_list.forEach(function(program_id_check) {
        program_id_check.addEventListener('change', updateSelectionCount);
    });
};

function countMaterials(count, duration) {
    let totalCount = document.getElementById('total_count');
    totalCount.textContent = `Выбрано: ${count}`;
    let totalDur = document.getElementById('total_dur');
    totalDur.textContent = `Общий хронометраж: ${convertFramesToTime(duration)}`;
};

document.getElementById('search_input').addEventListener('keyup', fastSearch);
document.getElementById('search_type').addEventListener('change', fastSearch);

function fastSearch() {
    let filter = document.getElementById('search_input').value.toLowerCase();
    let tableBody = document.getElementById('tableBody');
    let rows = tableBody.getElementsByTagName('tr');
    let searchSettings = document.getElementById('search_type').value;
    if (searchSettings == 0) {
        for (let i = 0; i < rows.length; i++) {
            let nameCell = rows[i].getElementsByTagName('td')[0];
            if (nameCell) {
                let idValue = nameCell.querySelector('input')?.value
                rows[i].style.display = idValue.indexOf(filter) > -1 ? '' : 'none';
            }
        }
    }
    if (searchSettings == 1) {
        for (let i = 0; i < rows.length; i++) {
            let nameCell = rows[i].getElementsByTagName('td')[2];
            if (nameCell) {
                let clipIdValue = nameCell.querySelector('input')?.value
                rows[i].style.display = clipIdValue.indexOf(filter) > -1 ? '' : 'none';
            }
        }
    }
    if (searchSettings == 2) {
        for (let i = 0; i < rows.length; i++) {
            let nameCell = rows[i].getElementsByTagName('td')[1];
            if (nameCell) {
                let textValue = (nameCell.textContent || nameCell.innerText).toLowerCase();
                rows[i].style.display = textValue.indexOf(filter) > -1 ? '' : 'none';
            }
        }
    }
    if (searchSettings == 3) {
        for (let i = 0; i < rows.length; i++) {
            let nameCell = rows[i].getElementsByTagName('td')[4];
            if (nameCell) {
                let textValue = (nameCell.textContent || nameCell.innerText).toLowerCase();
                rows[i].style.display = textValue.indexOf(filter) > -1 ? '' : 'none';
            }
        }
    }
};

function convertFramesToTime(frames, fps = 25) {
    if (isNaN(frames) || frames === null || frames === undefined) {
            frames = 0;
    };
    const sec = parseInt(frames) / fps;
    const yy = Math.floor(Math.floor(sec / 3600 / 24) / 365);
    const dd = Math.floor(Math.floor(sec / 3600 / 24) % 365);
    const hh = Math.floor((sec / 3600) % 24);
    const mm = Math.floor((sec % 3600) / 60);
    const ss = Math.floor((sec % 3600) % 60);
    const ff = Math.floor((sec % 1) * fps);

    const formatNum = num => num.toString().padStart(2, '0');

    if (yy < 1) {
        if (dd < 1) {
            return `${formatNum(hh)}:${formatNum(mm)}:${formatNum(ss)}`;
        } else {
            return `${formatNum(dd)}д. ${formatNum(hh)}:${formatNum(mm)}:${formatNum(ss)}`;
        }
    } else {
        if (0 < yy % 10 && yy % 10 < 5) {
            return `${formatNum(yy)}г. ${formatNum(dd)}д. ${formatNum(hh)}:${formatNum(mm)}:${formatNum(ss)}`;
        } else {
            return `${formatNum(yy)}л. ${formatNum(dd)}д. ${formatNum(hh)}:${formatNum(mm)}:${formatNum(ss)}`;
        }
    }
};

function thousands(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
};

function CopyText(input) {
    input.focus()
    input.select()
    document.execCommand('copy');
};

function ShowApproveFinal() {
    let checked_list = document.getElementsByName('program_id_check');
    let program_id_list = [];
    let approveList = document.getElementById('approve_list')
    approveList.dataset.approveList = ''
    for (let i = 0; i < checked_list.length; i++) {
        if (checked_list[i].checked) {
            program_id_list.push(checked_list[i].value);}
        }
    if (program_id_list.length > 0) {
        const ApproveFinalModal = bootstrap.Modal.getInstance(document.getElementById('ApproveFinalModal')) ||
            new bootstrap.Modal(document.getElementById('ApproveFinalModal'));
        ApproveFinalModal.show();
        approveList.dataset.approveList = JSON.stringify(program_id_list);
    }
    else {
        console.log('error', 'Ни одна задача не выбрана!');
        const errorModal = bootstrap.Modal.getInstance(document.getElementById('errorModal')) ||
            new bootstrap.Modal(document.getElementById('errorModal'));
        document.getElementById('error_message').textContent = 'Ни одна задача не выбрана!';
        errorModal.show();
    }
};

function ShowFinalFail() {
    let full_list = document.getElementsByName('program_id_check');
    let checked_program_id_list = [];
    let checked_list = [];
    let finalFailList = document.getElementById('final_fail_list')
    finalFailList.dataset.finalFailList = ''
    failContainer = document.getElementById('fail_container')
    failContainer.innerHTML = ''
    for (let i = 0; i < full_list.length; i++) {
        if (full_list[i].checked) {
            checked_list.push(full_list[i]);
            checked_program_id_list.push(full_list[i].value);
        }
    }
    if (checked_list.length > 0) {
        const FinalFailModal = bootstrap.Modal.getInstance(document.getElementById('FinalFailModal')) ||
            new bootstrap.Modal(document.getElementById('FinalFailModal'));
        FinalFailModal.show();
        for (let i = 0; i < checked_list.length; i++) {
            let material = document.createElement("div");
            material.className = 'material'
            failContainer.appendChild(material);

            let prog_id = checked_list[i].dataset.programId
            let f_name = checked_list[i].dataset.fileName
            let prodYear = checked_list[i].dataset.prodYear
            let f_path = checked_list[i].dataset.filePath
            let worker_id = checked_list[i].dataset.workerId

            let final_fail_prog_id = document.createElement("input");
            final_fail_prog_id.type = 'hidden';
            final_fail_prog_id.name = 'final_fail_prog_id';
            final_fail_prog_id.value = prog_id;
            material.appendChild(final_fail_prog_id);

            let file_name = document.createElement("h5");
            file_name.classList.add('my-2');
            file_name.textContent = `${f_name} (${prodYear || ''})`;
            file_name.name = 'file_name'
            material.appendChild(file_name);

            let sub_header = document.createElement("h6");
            sub_header.textContent = 'Комментарий по необходимой доработке';
            material.appendChild(sub_header);

            let final_fail_comment = document.createElement("textarea");
            final_fail_comment.classList.add('form-control');
            final_fail_comment.classList.add('my-2');
            final_fail_comment.name = 'final_fail_comment';
            final_fail_comment.style = 'min-height: 130px';
            final_fail_comment.placeholder = '1. Таймкод - суть проблемы\n2. Таймкод - суть проблемы\n3. ...';
            material.appendChild(final_fail_comment);

            let final_fail_worker_id = document.createElement("input");
            final_fail_worker_id.type = 'hidden';
            final_fail_worker_id.name = 'final_fail_worker_id';
            final_fail_worker_id.value = worker_id;
            material.appendChild(final_fail_worker_id);

            let deadline_name = document.createElement("h6");
            deadline_name.textContent = 'Установить крайний срок'
            deadline_name.classList.add('my-2');
            material.appendChild(deadline_name);

            let deadline = document.createElement("input");
            deadline.type = 'date';
            deadline.classList.add('form-control');
            deadline.name = 'deadline'
            material.appendChild(deadline);

            let validator = document.createElement("div");
            validator.classList.add('invalid-feedback')
            validator.textContent = 'Необходимо заполнить'
            material.appendChild(validator);

            let btnGroupName = document.createElement("h6");
            btnGroupName.textContent = 'Кто должен исправить?'
            btnGroupName.classList.add('my-2');
            material.appendChild(btnGroupName);

            let btnGroup = document.createElement('div');
            btnGroup.className = 'btn-group btn-group-sm';
            btnGroup.role = 'group';
            btnGroup.id = `final_fail_recipient_${prog_id}`;
            const groupName = `final_fail_recipient_${prog_id}`;

            const radioWorker = document.createElement('input');
            const radioWorkerId = `radioWorker_${prog_id}`;
            radioWorker.type = 'radio';
            radioWorker.className = 'btn-check';
            radioWorker.id = radioWorkerId;
            radioWorker.name = groupName;
            radioWorker.autocomplete = 'off';
            radioWorker.value = worker_id;
            radioWorker.checked = true;

            const labelWorker = document.createElement('label');
            labelWorker.className = 'btn btn-outline-secondary';
            labelWorker.htmlFor = radioWorkerId;
            labelWorker.textContent = 'Инженер подготовки';

            const radioOTK = document.createElement('input');
            const radioOTKId = `radioOTK_${prog_id}`;
            radioOTK.type = 'radio';
            radioOTK.className = 'btn-check';
            radioOTK.id = radioOTKId;
            radioOTK.name = groupName;
            radioOTK.autocomplete = 'off';
            radioOTK.value = 'otk';

            const labelOTK = document.createElement('label');
            labelOTK.className = 'btn btn-outline-secondary';
            labelOTK.htmlFor = radioOTKId;
            labelOTK.textContent = 'ОТК';

            // Добавляем в группу
            btnGroup.appendChild(radioWorker);
            btnGroup.appendChild(labelWorker);
            btnGroup.appendChild(radioOTK);
            btnGroup.appendChild(labelOTK);
            material.appendChild(btnGroup);

            let divider = document.createElement("hr");
            divider.style = 'width: 40%; size: 2;';
            material.appendChild(divider);
        };
//        finalFailList.dataset.finalFailList = JSON.stringify(checked_program_id_list);
    }
    else {
        console.log('error');
        const errorModal = bootstrap.Modal.getInstance(document.getElementById('errorModal')) ||
            new bootstrap.Modal(document.getElementById('errorModal'));
        document.getElementById('error_message').textContent = 'Ни одна задача не выбрана!';
        errorModal.show();
    }

};

function finalFail() {
    let failData = [];
    let failContainer = document.getElementById('fail_container');
    let materialList = failContainer.querySelectorAll('.material');
    console.log(materialList);
    materialList.forEach(container => {
        const programId = container.querySelector('[name="final_fail_prog_id"]')?.value;
        const comment = container.querySelector('[name="final_fail_comment"]')?.value || '';
        const deadline = container.querySelector('[name="deadline"]')?.value;

        // Ищем выбранную радиокнопку в этом контейнере
        const selectedRecipient = container.querySelector('input[type="radio"]:checked');
        const recipient = selectedRecipient ? selectedRecipient.value : null;

        if (programId) {
            failData.push({
                program_id: programId,
                deadline: deadline,
                recipient: recipient,
                comment: comment
            });
        }
    });
    fetch('/on-air-report/final_fail_batch/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'),
        'X-Requested-With': 'XMLHttpRequest'
    },
    body: JSON.stringify(failData),
    credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            window.location.reload();
        }
        else {
            console.log('error', data.message)

            const FinalFailModal = bootstrap.Modal.getInstance(document.getElementById('FinalFailModal')) ||
                        new bootstrap.Modal(document.getElementById('FinalFailModal'));
            const errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
            document.getElementById('error_message').textContent = data.message;

            FinalFailModal.hide();
            errorModal.toggle();
        }
    })
    .catch(error => {
        console.error('Error sending info:', error);
    });
};

function approveFinal() {
    let approveList = JSON.parse(document.getElementById('approve_list').dataset.approveList)
    fetch('/on-air-report/apply_final_batch/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'),
        'X-Requested-With': 'XMLHttpRequest'
    },
    body: JSON.stringify(approveList),
    credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            window.location.reload();
        }
        else {
            console.log('error', data.message)

            const ApproveFinalModal = bootstrap.Modal.getInstance(document.getElementById('ApproveFinalModal')) ||
                        new bootstrap.Modal(document.getElementById('ApproveFinalModal'));
            const errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
            document.getElementById('error_message').textContent = data.message;

            ApproveFinalModal.hide();
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