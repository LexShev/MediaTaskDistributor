document.addEventListener('DOMContentLoaded', function() {
    fetch('/otk/load_otk_task_table/')
        .then(response => response.json())
        .then(data => {
            document.getElementById('otk_task_table').innerHTML = data.html;
            updateMainProgramId();
            fastSearch();
            totalCalc();
        })
        .catch(error => {
            document.getElementById('otk_task_table').innerHTML = `
                <div class="alert alert-danger">Ошибка загрузки данных</div>
            `;
    });
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

function adjustTextarea(dropdown) {
    let textarea_list = dropdown.parentElement.getElementsByTagName('textarea');
    Array.from(textarea_list).forEach(function(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = (textarea.scrollHeight+10) + 'px';
    });
};

function changeProgramIdCheckbox() {
    let fullSelectCheckbox = document.getElementById('full_select');
    let tableBody = document.getElementById('tableBody');
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

function updateMainProgramId() {
    let fullSelectCheckbox = document.getElementById('full_select');
    let program_id_check_list = document.getElementsByName('program_id_check');
    program_id_check_list.forEach(function(program_id_check) {
        program_id_check.addEventListener('change', changeFullSelect);
    });

    function changeFullSelect() {
        let checked_list = [];
        for (let i = 0; i < program_id_check_list.length; i++) {
            if (program_id_check_list[i].checked) {
                checked_list.push(program_id_check_list[i]);
            }
        };
        if (0 < checked_list.length && checked_list.length < program_id_check_list.length) {
            fullSelectCheckbox.indeterminate = true;
            fullSelectCheckbox.checked = false;
        }
        else if (checked_list.length == program_id_check_list.length) {
            fullSelectCheckbox.indeterminate = false;
            fullSelectCheckbox.checked = true;
        }
        else if (checked_list.length == 0) {
            fullSelectCheckbox.indeterminate = false;
            fullSelectCheckbox.checked = false;
        }
    };
};

function ShowApproveOTK() {
    let OTKList = document.getElementById('otk_list');
    OTKList.innerHTML = '';

    let checked_list = document.getElementsByName('program_id_check');
    let program_id_list = [];
    for (let i = 0; i < checked_list.length; i++) {
        if (checked_list[i].checked) {
            let program_id = checked_list[i].dataset.programId;
            let old_file_name = checked_list[i].dataset.programName;
            let old_file_path = checked_list[i].dataset.filePath;
            let worker_id = checked_list[i].dataset.workerId;
            let sender = checked_list[i].dataset.sender;
            program_id_list.push(checked_list[i].value);

            let OTKContainer = document.createElement("div");
            OTKContainer.id = `otk_container_${program_id}`
            OTKContainer.dataset.programId = program_id;
            OTKContainer.dataset.oldFilePath = old_file_path;
            OTKContainer.classList.add('otk_container')

            let otk_program_id = document.createElement("input");
            otk_program_id.type = 'hidden';
            otk_program_id.name = 'otk_program_id';
            otk_program_id.value = program_id;
            OTKContainer.appendChild(otk_program_id);

            let file_name = document.createElement("h5");
            file_name.classList.add('my-2');
            file_name.textContent = old_file_name;
            file_name.name = 'file_name'
            OTKContainer.appendChild(file_name);

            let file_path_header = document.createElement("h6");
            file_path_header.textContent = 'Новый путь к файлу';
            OTKContainer.appendChild(file_path_header);

            let filePathContainer = document.createElement('div');
            filePathContainer.classList.add('d-flex');
            filePathContainer.name = 'filePathContainer';
            OTKContainer.appendChild(filePathContainer);

            let switchContainer = document.createElement('div');
            switchContainer.classList.add('btn-group-vertical', 'm-2');
            switchContainer.role = 'group';
            filePathContainer.appendChild(switchContainer);

            let cenz_switcher = document.createElement("input");
            cenz_switcher.classList.add('btn-check');
            cenz_switcher.type = 'radio';
            cenz_switcher.name = `switcher_${program_id}`;
            cenz_switcher.id = `cenz_switcher_${program_id}`;
            cenz_switcher.value = 'cenz';
            cenz_switcher.autocomplete = 'off';
            cenz_switcher.setAttribute('checked', true);
            switchContainer.appendChild(cenz_switcher);

            let cenzSwitchLabel = document.createElement("label");
            cenzSwitchLabel.classList.add('btn', 'btn-outline-success');
            cenzSwitchLabel.textContent = 'CENZ';
            cenzSwitchLabel.setAttribute('for', `cenz_switcher_${program_id}`);
            switchContainer.appendChild(cenzSwitchLabel);

            let fix_switcher = document.createElement("input");
            fix_switcher.classList.add('btn-check');
            fix_switcher.type = 'radio';
            fix_switcher.name = `switcher_${program_id}`;
            fix_switcher.id = `fix_switcher_${program_id}`;
            fix_switcher.value = 'fix';
            fix_switcher.autocomplete = 'off';
            switchContainer.appendChild(fix_switcher);

            let fixSwitchLabel = document.createElement("label");
            fixSwitchLabel.classList.add('btn', 'btn-outline-warning');
            fixSwitchLabel.textContent = 'FIX';
            fixSwitchLabel.setAttribute('for', `fix_switcher_${program_id}`);
            switchContainer.appendChild(fixSwitchLabel);

            let dropZoneRow = document.createElement("div");
            dropZoneRow.classList.add('col');
            filePathContainer.appendChild(dropZoneRow);

            let drop_zone = document.createElement("div");
            drop_zone.classList.add('col', 'drop-zone', 'border-secondary', 'text-center', 'text-secondary', 'p-2', 'my-2');
            dropZoneRow.appendChild(drop_zone);

            let drop_zone_text_1 = document.createElement("p");
            drop_zone_text_1.textContent = 'Перетащите файл сюда...';
            drop_zone_text_1.classList.add('my-2');
            drop_zone.appendChild(drop_zone_text_1);
            let drop_zone_text_2 = document.createElement("p");
            drop_zone_text_2.textContent = '(или кликните для выбора)';
            drop_zone_text_2.classList.add('my-2');
            drop_zone.appendChild(drop_zone_text_2);

            let otk_file_path_group = document.createElement("div");
            otk_file_path_group.classList.add('col', 'input-group', 'my-2');
            dropZoneRow.appendChild(otk_file_path_group);

            let otk_file_path = document.createElement("input");
            otk_file_path.classList.add('form-control');
            otk_file_path.setAttribute('accept', 'video/*');
            otk_file_path.setAttribute('type', 'file');
            otk_file_path.name = 'otk_file_path';
            otk_file_path.id = `otk_file_path_${program_id}`;
            otk_file_path_group.appendChild(otk_file_path);

            let invalid_feedback = document.createElement("div");
            invalid_feedback.classList.add('invalid-feedback');
            invalid_feedback.textContent = 'Необходимо указать файл'
            otk_file_path_group.appendChild(invalid_feedback);

            let otk_header = document.createElement("h6");
            otk_header.textContent = 'Комментарий';
            OTKContainer.appendChild(otk_header);

            let otk_comment = document.createElement("textarea");
            otk_comment.classList.add('form-control');
            otk_comment.classList.add('m-2');
            otk_comment.name = 'otk_comment';
            otk_comment.style = 'min-height: 50px';
            OTKContainer.appendChild(otk_comment);

            let divider = document.createElement("hr");
            divider.style = 'width: 40%; size: 2;';
            divider.classList.add('mb-4');
            OTKContainer.appendChild(divider);

            OTKList.appendChild(OTKContainer);
        }
    }
    if (program_id_list.length > 0) {
        ApproveOTK = new bootstrap.Modal(document.getElementById('ApproveOTK'));
        const OTKContainers = document.querySelectorAll('.otk_container');
        initializeDropZones(OTKContainers);
        ApproveOTK.toggle();
    }
    else {
        console.error('error');
        errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
        errorModal.toggle();
    }
};

function ShowFixReadyList() {
    let FixList = document.getElementById('fix_list');
    FixList.innerHTML = '';

    let checked_list = document.getElementsByName('program_id_check');
    let program_id_list = []
    for (let i = 0; i < checked_list.length; i++) {
        if (checked_list[i].checked) {
            program_id_list.push(checked_list[i].value);
        }
    }
    if (program_id_list.length > 0) {
        for (let i = 0; i < checked_list.length; i++) {
            if (checked_list[i].checked) {
                let program_id = checked_list[i].dataset.programId;
                let old_file_name = checked_list[i].dataset.programName;
                let old_file_path = checked_list[i].dataset.filePath;
                let worker_id = checked_list[i].dataset.workerId;
                let sender = checked_list[i].dataset.sender;

                let FIXContainer = document.createElement("div");
                FIXContainer.id = `fix_container_${program_id}`
                FIXContainer.dataset.programId = program_id;
                FIXContainer.dataset.ProgramName = old_file_name;
                FIXContainer.dataset.oldFilePath = old_file_path;
                FIXContainer.dataset.workerId = (worker_id && worker_id !== "None") ? worker_id : sender;
                FIXContainer.classList.add('fix_container')

                let fix_program_id = document.createElement("input");
                fix_program_id.type = 'hidden';
                fix_program_id.name = 'fix_program_id';
                fix_program_id.value = program_id;
                FIXContainer.appendChild(fix_program_id);

                let program_name = document.createElement("h5");
                program_name.classList.add('program_name', 'my-2');
                program_name.textContent = old_file_name;
                FIXContainer.appendChild(program_name);

                let file_path_header = document.createElement("h6");
                file_path_header.textContent = 'Новый путь к файлу';
                FIXContainer.appendChild(file_path_header);

                let drop_zone = document.createElement("div");
                drop_zone.classList.add('drop-zone', 'border-secondary', 'text-center', 'text-secondary', 'p-2', 'my-2');
                FIXContainer.appendChild(drop_zone);

                let drop_zone_text_1 = document.createElement("p");
                drop_zone_text_1.textContent = 'Перетащите файл сюда...';
                drop_zone_text_1.classList.add('my-2');
                drop_zone.appendChild(drop_zone_text_1);
                let drop_zone_text_2 = document.createElement("p");
                drop_zone_text_2.textContent = '(или кликните для выбора)';
                drop_zone_text_2.classList.add('my-2');
                drop_zone.appendChild(drop_zone_text_2);

                let fix_file_path_group = document.createElement("div");
                fix_file_path_group.classList.add('input-group', 'file-input-group', 'my-2');
                FIXContainer.appendChild(fix_file_path_group);

                let fix_file_path = document.createElement("input");
                fix_file_path.classList.add('form-control', 'rounded');
                fix_file_path.setAttribute('accept', 'video/*');
                fix_file_path.setAttribute('type', 'file');
                fix_file_path.name = 'fix_file_path';
                fix_file_path.id = `fix_file_path_${program_id}`;
                fix_file_path_group.appendChild(fix_file_path);

                let invalid_feedback = document.createElement("div");
                invalid_feedback.classList.add('invalid-feedback');
                invalid_feedback.textContent = 'Необходимо указать файл'
                fix_file_path_group.appendChild(invalid_feedback);

                let sub_header = document.createElement("h6");
                sub_header.textContent = 'Комментарий по исправлению';
                FIXContainer.appendChild(sub_header);

                let fix_comment = document.createElement("textarea");
                fix_comment.classList.add('form-control', 'my-2');
                fix_comment.name = 'fix_comment';
                fix_comment.style = 'min-height: 130px';
                fix_comment.placeholder = '1. Перекачан исходник\n2. Исправлен звук\n3. ...';
                FIXContainer.appendChild(fix_comment);

                let divider = document.createElement("hr");
                divider.style = 'width: 40%; size: 2;';
                FIXContainer.appendChild(divider);

                FixList.appendChild(FIXContainer);
            }
        }
        ApproveFIX = new bootstrap.Modal(document.getElementById('ApproveFIX'));
        ApproveFIX.toggle();
        const FIXContainers = document.querySelectorAll('.fix_container');
        initializeDropZones(FIXContainers);

    }
    else
        {
            console.log('error');
            errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
            errorModal.toggle();
        }
    };

function ShowOTKFail() {
    let OTKFailList = document.getElementById('otk_fail_list');
    OTKFailList.innerHTML = ''

    let checked_list = document.getElementsByName('program_id_check');
    let program_id_list = [];
    for (let i = 0; i < checked_list.length; i++) {
        if (checked_list[i].checked) {
            program_id_list.push(checked_list[i].value);}
    }
    if (program_id_list.length > 0) {
        for (let i = 0; i < checked_list.length; i++) {
            if (checked_list[i].checked) {
                let program_id = checked_list[i].dataset.programId
                let old_file_name = checked_list[i].dataset.programName
                let old_file_path = checked_list[i].dataset.filePath
                let worker_id = checked_list[i].dataset.workerId

                let FailContainer = document.createElement("div");
                FailContainer.id = `fail_container_${program_id}`
                FailContainer.dataset.programId = program_id;
                FailContainer.dataset.ProgramName = old_file_name;
                FailContainer.dataset.oldFilePath = old_file_path;
                FailContainer.dataset.workerId = (worker_id && worker_id !== "None") ? worker_id : sender;
                FailContainer.classList.add('fail_container')

                let otk_fail_program_id = document.createElement("input");
                otk_fail_program_id.type = 'hidden';
                otk_fail_program_id.name = 'otk_fail_program_id';
                otk_fail_program_id.value = program_id;
                FailContainer.appendChild(otk_fail_program_id);

                let file_name = document.createElement("h5");
                file_name.classList.add('my-2');
                file_name.textContent = old_file_name;
                FailContainer.appendChild(file_name);

                let sub_header = document.createElement("h6");
                sub_header.textContent = 'Комментарий по необходимой доработке';
                FailContainer.appendChild(sub_header);

                let otk_fail_comment = document.createElement("textarea");
                otk_fail_comment.classList.add('form-control', 'my-2');
                otk_fail_comment.name = 'otk_fail_comment';
                otk_fail_comment.style = 'min-height: 130px';
                otk_fail_comment.placeholder = '1. Таймкод - суть проблемы\n2. Таймкод - суть проблемы\n3. ...';
                FailContainer.appendChild(otk_fail_comment);

                let otk_fail_worker_id = document.createElement("input");
                otk_fail_worker_id.type = 'hidden';
                otk_fail_worker_id.name = 'otk_fail_worker_id';
                otk_fail_worker_id.value = worker_id;
                OTKFailList.appendChild(otk_fail_worker_id);

                let divider = document.createElement("hr");
                divider.style = 'width: 40%; size: 2;';
                FailContainer.appendChild(divider);

                OTKFailList.appendChild(FailContainer);
            }
        }
        OTKFail = new bootstrap.Modal(document.getElementById('OTKFail'));
        OTKFail.toggle();
    }
    else {
        console.log('error');
        errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
        errorModal.toggle();
    }
};

function setStatusOTK() {
    let OTKContainers = document.querySelectorAll('.otk_container');
    let otkData = [];
    OTKContainers.forEach(container => {
        let programId = container?.dataset.programId || ''
        let otk_comment = container.querySelector("textarea[name='otk_comment']");
        let otk_file_path = container.querySelector("input[name='otk_file_path']");
        let selectedRadio = container.querySelector(`input[name='switcher_${programId}']:checked`);

        otkData.push([
            programId,
            otk_comment?.value || '',
            container?.dataset.oldFilePath || '',
            container?.dataset.fileName || '',
            otk_file_path?.files?.[0]?.name || '',
            selectedRadio ? selectedRadio.value : 'cenz'
        ])
    });

    fetch('/otk/set_status_otk/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify(otkData),
        credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                window.location.href = `/otk/`;
            }
            else {
                console.log('error', data.message)

                const ApproveOTK = bootstrap.Modal.getInstance(document.getElementById('ApproveOTK')) ||
                            new bootstrap.Modal(document.getElementById('ApproveOTK'));
                const errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
                error_message = document.getElementById('error_message');
                error_message.textContent = data.message;

                ApproveOTK.hide();
                errorModal.toggle();
            }
        })
        .catch(error => {
            console.error('Error sending info:', error);
        });
};

function setStatusFIX() {
    let FixList = document.getElementById('fix_list');
    let OTKContainers = FixList.querySelectorAll('.fix_container');
    let fixData = [];
    OTKContainers.forEach(container => {
        let fix_comment = container.querySelector("textarea[name='fix_comment']");
        let fix_file_path = container.querySelector("input[name='fix_file_path']");
        fixData.push([
            container?.dataset.programId || '',
            fix_comment?.value || '',
            container?.dataset.oldFilePath || '',
            container?.dataset.ProgramName || '',
            fix_file_path?.files?.[0]?.name || '',
            container?.dataset.workerId || '',
        ])
    });

    fetch('/otk/set_status_fix_ready/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify(fixData),
        credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                window.location.href = `/otk/`;
            }
            else {
                console.log('error', data.message)

                const ApproveFIX = bootstrap.Modal.getInstance(document.getElementById('ApproveFIX')) ||
                            new bootstrap.Modal(document.getElementById('ApproveFIX'));
                const errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
                error_message = document.getElementById('error_message');
                error_message.textContent = data.message;

                ApproveFIX.hide();
                errorModal.toggle();
            }
        })
        .catch(error => {
            console.error('Error sending info:', error);
        });
};

function setStatusOTKFail() {
    let FailList = document.getElementById('otk_fail_list');
    let OTKContainers = FailList.querySelectorAll('.fail_container');
    let failData = [];
    OTKContainers.forEach(container => {
        let fail_comment = container.querySelector("textarea[name='otk_fail_comment']");
        failData.push([
            container?.dataset.programId || '',
            fail_comment?.value || '',
            container?.dataset.ProgramName || '',
            container?.dataset.workerId || '',
        ])
    });
    fetch('/otk/set_status_fix_ready/', {
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
                window.location.href = `/otk/`;
            }
            else {
                console.log('error', data.message)

                const OTKFail = bootstrap.Modal.getInstance(document.getElementById('OTKFail')) ||
                            new bootstrap.Modal(document.getElementById('OTKFail'));
                const errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
                error_message = document.getElementById('error_message');
                error_message.textContent = data.message;

                OTKFail.hide();
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

function ShowOTKComment() {
    const comment_dict = document.getElementById('comment').dataset.comment;
    const jsonStr = comment_dict.replace(/'/g, '"').replace(/None/g, 'null').replace(/\r\n/g, '\\n').replace(/\\"/g, '"');
    const commentArray = JSON.parse(jsonStr);

    let OTKCommentTitle = document.getElementById('otk_comment_title');
    OTKCommentTitle.innerHTML = ''
    OTKCommentTitle.textContent = commentArray[0].Progs_name
    let OTKCommentBody = document.getElementById('otk_comment_body');
    OTKCommentBody.innerHTML = ''

    for (let i = 0; i < commentArray.length; i++) {

        deadline = document.createElement("h6");
        deadline.textContent = `Исправить до: ${commentArray[i].deadline}`;
        OTKCommentBody.appendChild(deadline);

        comment_text = document.createElement("textarea");
        comment_text.classList.add('form-control');
        comment_text.style = 'min-height: 60px';
        comment_text.disabled = true
        comment_text.textContent = commentArray[i].comment;
        comment_text.rows = comment_text.value.split(/\r|\r\n|\n/).length;
        OTKCommentBody.appendChild(comment_text);

        let divider = document.createElement("hr");
        divider.style = 'width: 40%; size: 2;';
        OTKCommentBody.appendChild(divider);

    };
    OTKComment = new bootstrap.Modal(document.getElementById('OTKComment'), {keyboard: true});
    OTKComment.toggle();

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
            let nameCell = rows[i].getElementsByTagName('td')[1];
            if (nameCell) {
                let textValue = (nameCell.textContent || nameCell.innerText).toLowerCase();
                rows[i].style.display = textValue.indexOf(filter) > -1 ? '' : 'none';
            }
        }
    }
    if (searchSettings == 2) {
        for (let i = 0; i < rows.length; i++) {
            let nameCell = rows[i].getElementsByTagName('td')[3];
            if (nameCell) {
                let textValue = (nameCell.textContent || nameCell.innerText).toLowerCase();
                rows[i].style.display = textValue.indexOf(filter) > -1 ? '' : 'none';
            }
        }
    }
};

document.getElementById('search_input').addEventListener('keyup', totalCalc);
function totalCalc() {
    let tableBody = document.getElementById('tableBody');
    let rows = tableBody.getElementsByTagName('tr');
    let totalNum = document.getElementById('total_num');
    let totalDuration = document.getElementById('total_dur');
    let visibleCount = 0;
    let countDuration = 0;
    for (let i = 0; i < rows.length; i++) {
        if (rows[i].style.display !== 'none') {
            let input = rows[i].getElementsByTagName('td')[6].querySelector('input');
            let duration = parseFloat(input?.value || 0);
            countDuration+=duration;
            visibleCount++;
        }
    };
    totalNum.textContent = `Всего: ${thousands(visibleCount)}`;
    totalDuration.textContent = `Продолжительность: ${convertFramesToTime(countDuration)}`;
    return visibleCount;
};

function ResetFilter() {
    const [readyDate, schedDate, deadline, workerId, materialType, schedId, taskStatus] =
    ['ready_date', 'sched_date', 'deadline', 'worker_id', 'material_type', 'sched_id', 'task_status', 'search_input']
    .map(id => document.getElementById(id));

    [readyDate, schedDate, deadline, workerId, materialType, schedId, taskStatus, search_input].forEach(el => {el.value = '';});

    document.getElementById('otk_form').submit();

};

function initializeDropZones(containers) {

    containers.forEach(container => {
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
                const firstFile = files[0];
                const dataTransfer = new DataTransfer();
                dataTransfer.items.add(firstFile);
                fileInput.files = dataTransfer.files;
                const event = new Event('change', { bubbles: true });
                fileInput.dispatchEvent(event);
                updateDropZoneAppearance();
            }
        }

        // Клик по зоне тоже открывает выбор файла
        dropZone.addEventListener('click', function(e) {
            if (e.target !== fileInput) {
                fileInput.click();
            }
        });

        // Обработчик изменения файла через стандартный диалог
        fileInput.addEventListener('change', function() {
            if (this.files.length > 0) {
                updateDropZoneAppearance();
            } else {
                resetDropZoneAppearance();
            }
        });

        // Функция обновления внешнего вида
        function updateDropZoneAppearance() {
            console.log('updateDropZoneAppearance called for container');

            const fileName = fileInput?.files?.[0]?.name || '';

            if (!fileName) {
                console.log('No file selected, resetting appearance');
                resetDropZoneAppearance();
                return;
            }

            // Обновляем классы
            dropZone.classList.remove('border-secondary', 'text-secondary');
            dropZone.classList.add('file-selected', 'border-success', 'text-success');
            fileInput.classList.remove('border-secondary', 'text-secondary');
            fileInput.classList.add('border-success', 'text-success');

            let oldFilePath = container?.dataset.oldFilePath || '';
            const programId = container.dataset.programId;

            // Получаем радио-кнопку
            const selectedRadio = container.querySelector(`input[name="switcher_${programId}"]:checked`);
            let mode = 'fix';

            if (selectedRadio) {
                mode = selectedRadio.value;
            } else {
                // Если ни одна не выбрана, ищем checked атрибут
                const checkedRadio = container.querySelector(`input[name="switcher_${programId}"][checked]`);
                if (checkedRadio) {
                    mode = checkedRadio.value;
                }
            }

            let newFilePath;
            if (mode === 'cenz') {
                let currentCenzDir = document.getElementById('settings')?.dataset.currentCenzDir;
                newFilePath = currentCenzDir + '\\' + fileName;
            } else {
                // Для FIX: берем путь до папки из старого файла + новое имя файла
                const lastBackslashIndex = oldFilePath.lastIndexOf('\\');
                if (lastBackslashIndex !== -1) {
                    const directoryPath = oldFilePath.substring(0, lastBackslashIndex + 1);
                    newFilePath = directoryPath + fileName;
                } else {
                    // Если нет бэкслешей, просто используем имя файла
                    newFilePath = fileName;
                }
            }

            const paragraphs = dropZone.querySelectorAll('p');
            if (paragraphs.length >= 2) {
                paragraphs[0].textContent = `Старый файл: ${oldFilePath}`;
                paragraphs[1].textContent = `Новый файл: ${newFilePath}`;
            } else if (paragraphs.length === 1) {
                paragraphs[0].textContent = `Выбран файл: ${newFilePath}`;
            }

            // Сохраняем путь и режим
            container.dataset.newFilePath = newFilePath;
            container.dataset.selectedMode = mode;
        }

        // Функция сброса внешнего вида
        function resetDropZoneAppearance() {
            dropZone.classList.remove('file-selected', 'border-success', 'text-success');
            dropZone.classList.add('border-secondary', 'text-secondary');
            fileInput.classList.remove('border-success', 'text-success');
            fileInput.classList.add('border-secondary', 'text-secondary');

            const paragraphs = dropZone.querySelectorAll('p');
            if (paragraphs.length >= 2) {
                paragraphs[0].textContent = 'Перетащите файл сюда...';
                paragraphs[1].textContent = '(или кликните для выбора)';
            } else if (paragraphs.length === 1) {
                paragraphs[0].textContent = 'Перетащите файл сюда...';
                if (dropZone.children.length === 1) {
                    const secondParagraph = document.createElement('p');
                    secondParagraph.textContent = '(или кликните для выбора)';
                    secondParagraph.classList.add('my-2');
                    dropZone.appendChild(secondParagraph);
                }
            }

            // Удаляем путь
            if (container.dataset.newFilePath) {
                delete container.dataset.newFilePath;
            }
            if (container.dataset.selectedMode) {
                delete container.dataset.selectedMode;
            }
        }

        const switchContainer = container.querySelector('.btn-group-vertical');
        if (switchContainer) {
            const programId = container.dataset.programId;
            const cenzSwitcher = document.getElementById(`cenz_switcher_${programId}`);
            const fixSwitcher = document.getElementById(`fix_switcher_${programId}`);
            const cenzLabel = document.querySelector(`label[for="cenz_switcher_${programId}"]`);
            const fixLabel = document.querySelector(`label[for="fix_switcher_${programId}"]`);

            if (cenzSwitcher && fixSwitcher && cenzLabel && fixLabel) {
                // Функция для обновления при изменении радио-кнопки
                function handleRadioChange() {
                    if (fileInput && fileInput.files.length > 0) {
                        updateDropZoneAppearance();
                    }
                }

                // Обработчики для радио-кнопок
                cenzSwitcher.addEventListener('change', handleRadioChange);
                fixSwitcher.addEventListener('change', handleRadioChange);

                // Обработчики для лейблов
                cenzLabel.addEventListener('click', function() {
                    setTimeout(handleRadioChange, 10);
                });

                fixLabel.addEventListener('click', function() {
                    setTimeout(handleRadioChange, 10);
                });
            }
        }

        // Инициализация начального состояния
        if (fileInput && fileInput.files.length > 0) {
            updateDropZoneAppearance();
        }
    });
}

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
