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
    console.log(countDuration);

    totalNum.textContent = `Всего: ${thousands(visibleCount)}`;
    totalDuration.textContent = `Продолжительность: ${convertFramesToTime(countDuration)}`;
    return visibleCount;
};

