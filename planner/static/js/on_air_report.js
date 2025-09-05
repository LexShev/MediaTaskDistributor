document.addEventListener('DOMContentLoaded', function() {
    const channelContainer = document.querySelectorAll('.channel-container');
    channelContainer.forEach(channel => {
        const scheduleId = channel.dataset.scheduleId;
        const scheduleDate = channel.dataset.scheduleDate;
        fetch(`/on-air-report/get_schedule_table/${scheduleDate}/${scheduleId}`)
            .then(response => response.json())
            .then(data => {
                channel.innerHTML = data.html;
            })
            .catch(error => {
                console.error('Error loading day data:', error);
            });
    })
});

function changeProgramIdCheckbox(fullSelectCheckbox) {
    let tableBody = fullSelectCheckbox.closest('table').querySelector('tbody');
    let visibleCheckboxes = tableBody.querySelectorAll('tr:not([style*="display: none"]) input[name="program_id_check"]');
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
        console.log('error');
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
            let engineer_id = checked_list[i].dataset.engineerId

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

            let btnGroup = document.createElement('div');
            btnGroup.className = 'btn-group btn-group-sm';
            btnGroup.role = 'group';
            btnGroup.id = `final_fail_recipient_${prog_id}`;
            const groupName = `final_fail_recipient_${prog_id}`;

            const radioEngineer = document.createElement('input');
            const radioEngineerId = `radioEngineer_${prog_id}`;
            radioEngineer.type = 'radio';
            radioEngineer.className = 'btn-check';
            radioEngineer.id = radioEngineerId;
            radioEngineer.name = groupName;
            radioEngineer.autocomplete = 'off';
            radioEngineer.value = engineer_id;
            radioEngineer.checked = true;

            const labelEngineer = document.createElement('label');
            labelEngineer.className = 'btn btn-outline-secondary';
            labelEngineer.htmlFor = radioEngineerId;
            labelEngineer.textContent = 'Инженер подготовки';

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
            btnGroup.appendChild(radioEngineer);
            btnGroup.appendChild(labelEngineer);
            btnGroup.appendChild(radioOTK);
            btnGroup.appendChild(labelOTK);
            material.appendChild(btnGroup);

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

            let final_fail_engineer_id = document.createElement("input");
            final_fail_engineer_id.type = 'hidden';
            final_fail_engineer_id.name = 'final_fail_engineer_id';
            final_fail_engineer_id.value = engineer_id;
            material.appendChild(final_fail_engineer_id);

            let deadline_name = document.createElement("h6");
            deadline_name.textContent = 'Установить крайний срок'
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
        
        // Ищем выбранную радиокнопку в этом контейнере
        const selectedRecipient = container.querySelector('input[type="radio"]:checked');
        const recipient = selectedRecipient ? selectedRecipient.value : null;

        if (programId) {
            failData.push({
                program_id: programId,
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