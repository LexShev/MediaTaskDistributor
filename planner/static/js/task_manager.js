window.addEventListener('load', function() {
    let fullSelectCheckbox = document.getElementById('full_select');
    let program_id_check_list = document.getElementsByName('program_id_check');
    program_id_check_list.forEach(function(program_id_check) {
        program_id_check.addEventListener('change', changeFullSelect);
    });

    let textarea_list = document.getElementsByTagName('textarea');
    Array.from(textarea_list).forEach(function(textarea) {
        textarea.rows = textarea.value.split(/\r|\r\n|\n/).length;
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
});

document.addEventListener('DOMContentLoaded', function() {
    fetch('/task_manager/load_admin_task_table/')
        .then(response => response.json())
        .then(data => {
            document.getElementById('admin_task_table').innerHTML = data.html;
            fastSearch();
            totalCalc();
        })
        .catch(error => {
            document.getElementById('admin_task_table').innerHTML = `
                <div class="alert alert-danger">Ошибка загрузки данных</div>
            `;
    });
});

function changeProgramIdCheckbox() {
    let fullSelectCheckbox = document.getElementById('full_select');
    let program_id_check_list = document.getElementsByName('program_id_check');
    let checked_list = [];
        for (let i = 0; i < program_id_check_list.length; i++) {
            if (program_id_check_list[i].checked) {
                checked_list.push(program_id_check_list[i]);
            }
        };
    if (checked_list.length > 0) {
        fullSelectCheckbox.indeterminate = false;
        fullSelectCheckbox.checked = false;
        for (let i = 0; i < program_id_check_list.length; i++) {
            program_id_check_list[i].checked = false;
        };
    }
    else {
        fullSelectCheckbox.indeterminate = false;
        fullSelectCheckbox.checked = true;
        for (let i = 0; i < program_id_check_list.length; i++) {
            program_id_check_list[i].checked = true;
        };
    }
};

function showApproveTaskChange() {
    let checked_list = document.getElementsByName('program_id_check');
    let program_id_check_list = [];
    for (let i = 0; i < checked_list.length; i++) {
        if (checked_list[i].checked) {
            program_id_check_list.push(checked_list[i].value);}
        }
    if (program_id_check_list.length > 0) {
        ApproveTaskChange = new bootstrap.Modal(document.getElementById('ApproveTaskChange'));
        ApproveTaskChange.toggle();
    }
    else {
        console.log('error');
        errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
        errorModal.toggle();
    }
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

    document.getElementById('admin_form').submit();

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