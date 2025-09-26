document.addEventListener('DOMContentLoaded', function() {
    fetch('/on-air-report/load_on_air_task_table/')
        .then(response => response.json())
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
    const searchInput = document.querySelector('input[name="search_input"]');
    const dropdownMenu = document.getElementById('on_air_search_filter');

    // Показываем меню при фокусе
    searchInput.addEventListener('focus', function() {
        dropdownMenu.style.display = 'block';
    });

    // Скрываем меню при клике вне области
    document.addEventListener('click', function(event) {
        const isClickInsideInput = searchInput.contains(event.target);
        const isClickInsideMenu = dropdownMenu.contains(event.target);

        if (!isClickInsideInput && !isClickInsideMenu) {
            dropdownMenu.style.display = 'none';
        }
    });

    // Скрываем при Escape
    searchInput.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            dropdownMenu.style.display = 'none';
            searchInput.blur();
        }
    });

    // Предотвращаем закрытие при клике внутри меню
    dropdownMenu.addEventListener('mousedown', function(e) {
        e.stopPropagation();
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

function ResetFilter() {
    const [readyDate, schedDate, deadline, workerId, materialType, schedId, taskStatus] =
    ['ready_date', 'sched_date', 'deadline', 'worker_id', 'material_type', 'sched_id', 'task_status', 'search_input']
    .map(id => document.getElementById(id));

    [readyDate, schedDate, deadline, workerId, materialType, schedId, taskStatus, search_input].forEach(el => {el.value = '';});

    document.getElementById('otk_form').submit();

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