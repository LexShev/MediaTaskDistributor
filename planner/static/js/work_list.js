window.addEventListener('load', function() {
    let fullSelectCheckbox = document.getElementById('full_select');
    let program_id_list = document.getElementsByName('program_id');
    program_id_list.forEach(function(program_id) {
        program_id.addEventListener('change', changeFullSelect);
    });

    let textarea_list = document.getElementsByTagName('textarea');
    Array.from(textarea_list).forEach(function(textarea) {
        textarea.rows = textarea.value.split(/\r|\r\n|\n/).length;
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
    let program_id_list = document.getElementsByName('program_id');
    let checked_list = [];
        for (let i = 0; i < program_id_list.length; i++) {
            if (program_id_list[i].checked) {
                checked_list.push(program_id_list[i]);
            }
        };
    if (checked_list.length > 0) {
        fullSelectCheckbox.indeterminate = false;
        fullSelectCheckbox.checked = false;
        for (let i = 0; i < program_id_list.length; i++) {
            program_id_list[i].checked = false;
        };
    }
    else {
        fullSelectCheckbox.indeterminate = false;
        fullSelectCheckbox.checked = true;
        for (let i = 0; i < program_id_list.length; i++) {
            program_id_list[i].checked = true;
        };
    }
};

function ShowApproveOTK() {
    let checked_list = document.getElementsByName('program_id');
    let program_id_list = [];
    for (let i = 0; i < checked_list.length; i++) {
        if (checked_list[i].checked) {
            program_id_list.push(checked_list[i].value);}
        }
    if (program_id_list.length > 0) {
        ApproveOTK = new bootstrap.Modal(document.getElementById('ApproveOTK'));
        ApproveOTK.toggle();
    }
    else {
        console.log('error');
        errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
        errorModal.toggle();
    }
};

function ProgramIdList() {
    let FixList = document.getElementById('fix_list');
    FixList.innerHTML = ''

    let checked_list = document.getElementsByName('program_id');
    let program_id_list = []
    for (let i = 0; i < checked_list.length; i++) {
        if (checked_list[i].checked) {
            program_id_list.push(checked_list[i].value);
        }
    }
    if (program_id_list.length > 0) {
        ApproveFIX = new bootstrap.Modal(document.getElementById('ApproveFIX'));
        ApproveFIX.toggle();
        for (let i = 0; i < checked_list.length; i++) {
            if (checked_list[i].checked) {
                let prog_id = checked_list[i].dataset.programId
                let f_name = checked_list[i].dataset.fileName
                let f_path = checked_list[i].dataset.filePath
                let engineer_id = checked_list[i].dataset.engineerId
//                let [prog_id, f_name, f_path] = checked_list[i].value.split(';')

                let fix_prog_id = document.createElement("input");
                fix_prog_id.type = 'hidden';
                fix_prog_id.name = 'fix_prog_id';
                fix_prog_id.value = prog_id;
                FixList.appendChild(fix_prog_id);

                let file_name = document.createElement("h5");
                file_name.classList.add('my-2');
                file_name.textContent = f_name;
                file_name.name = 'file_name'
                FixList.appendChild(file_name);

                sub_header = document.createElement("h6");
                sub_header.textContent = 'Комментарий по исправлению';
                FixList.appendChild(sub_header);

                let fix_comment = document.createElement("textarea");
                fix_comment.classList.add('form-control');
                fix_comment.classList.add('my-2');
                fix_comment.name = 'fix_comment';
                fix_comment.style = 'min-height: 130px';
                fix_comment.placeholder = '1. Перекачан исходник\n2. Исправлен звук\n3. ...';
                FixList.appendChild(fix_comment);

                file_path_header = document.createElement("h6");
                file_path_header.textContent = 'Новый путь к файлу';
                FixList.appendChild(file_path_header);

                let fix_file_path = document.createElement("input");
                fix_file_path.classList.add('form-control');
                fix_file_path.classList.add('my-2');
                fix_file_path.name = 'fix_file_path';
                fix_file_path.type = 'text';
                fix_file_path.style = 'font-style: italic';
                fix_file_path.placeholder = `Старый: ${f_path}`;
                FixList.appendChild(fix_file_path);

                let fix_engineer_id = document.createElement("input");
                fix_engineer_id.type = 'hidden';
                fix_engineer_id.name = 'fix_engineer_id';
                fix_engineer_id.value = engineer_id;
                FixList.appendChild(fix_engineer_id);

                let divider = document.createElement("hr");
                divider.style = 'width: 40%; size: 2;';
                FixList.appendChild(divider);
            }
        }
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

    let checked_list = document.getElementsByName('program_id');
    let program_id_list = [];
    for (let i = 0; i < checked_list.length; i++) {
        if (checked_list[i].checked) {
            program_id_list.push(checked_list[i].value);}
    }
    if (program_id_list.length > 0) {
        OTKFail = new bootstrap.Modal(document.getElementById('OTKFail'));
        OTKFail.toggle();

        for (let i = 0; i < checked_list.length; i++) {
            if (checked_list[i].checked) {
                let prog_id = checked_list[i].dataset.programId
                let f_name = checked_list[i].dataset.fileName
                let f_path = checked_list[i].dataset.filePath
                let engineer_id = checked_list[i].dataset.engineerId
//                let [prog_id, f_name, f_path] = checked_list[i].value.split(';')

                let otk_fail_prog_id = document.createElement("input");
                otk_fail_prog_id.type = 'hidden';
                otk_fail_prog_id.name = 'otk_fail_prog_id';
                otk_fail_prog_id.value = prog_id;
                OTKFailList.appendChild(otk_fail_prog_id);

                let file_name = document.createElement("h5");
                file_name.classList.add('my-2');
                file_name.textContent = f_name;
                file_name.name = 'file_name'
                OTKFailList.appendChild(file_name);

                sub_header = document.createElement("h6");
                sub_header.textContent = 'Комментарий по необходимой доработке';
                OTKFailList.appendChild(sub_header);

                let otk_fail_comment = document.createElement("textarea");
                otk_fail_comment.classList.add('form-control');
                otk_fail_comment.classList.add('my-2');
                otk_fail_comment.name = 'otk_fail_comment';
                otk_fail_comment.style = 'min-height: 130px';
                otk_fail_comment.placeholder = '1. Таймкод - суть проблемы\n2. Таймкод - суть проблемы\n3. ...';
                OTKFailList.appendChild(otk_fail_comment);

                let otk_fail_engineer_id = document.createElement("input");
                otk_fail_engineer_id.type = 'hidden';
                otk_fail_engineer_id.name = 'otk_fail_engineer_id';
                otk_fail_engineer_id.value = engineer_id;
                OTKFailList.appendChild(otk_fail_engineer_id);

                let divider = document.createElement("hr");
                divider.style = 'width: 40%; size: 2;';
                OTKFailList.appendChild(divider);
            }
        }
    }
    else {
        console.log('error');
        errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
        errorModal.toggle();
    }
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

document.getElementById('tableFilter').addEventListener('keyup', fastSearch);
document.getElementById('search_type').addEventListener('change', fastSearch);

function fastSearch() {
    let filter = document.getElementById('tableFilter').value.toLowerCase();
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
};

document.getElementById('tableFilter').addEventListener('keyup', totalCalc);
function totalCalc() {
    let tableBody = document.getElementById('tableBody');
    let rows = tableBody.getElementsByTagName('tr');
    let totalNum = document.getElementById('total_num');
    let totalDuration = document.getElementById('total_dur');
    let visibleCount = 0;
    let countDuration = 0;
    for (let i = 0; i < rows.length; i++) {
        if (rows[i].style.display !== 'none') {
            let duration = parseFloat(rows[i].getElementsByTagName('td')[6].querySelector('input')?.value);
            countDuration+=duration;
            visibleCount++;
        }
    };

    totalNum.textContent = `Всего: ${thousands(visibleCount)}`;
    totalDuration.textContent = `Продолжительность: ${convertFramesToTime(countDuration)}`;
    return visibleCount;
};

function ResetFilter() {
    const [readyDate, schedDate, deadline, engineerId, materialType, schedId, taskStatus] =
    ['ready_date', 'sched_date', 'deadline', 'engineer_id', 'material_type', 'sched_id', 'task_status']
    .map(id => document.getElementById(id));

    [readyDate, schedDate, deadline, engineerId, materialType, schedId, taskStatus].forEach(el => {el.value = '';});

    document.getElementById('otk_form').submit();

};

function convertFramesToTime(frames, fps = 25) {
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