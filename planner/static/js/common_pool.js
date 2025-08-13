document.addEventListener('DOMContentLoaded', function() {
    fetch('/total-count/')
        .then(response => response.json())
        .then(data => {
            document.getElementById('total-count').textContent = thousands(data.total_count);
        });

    fetch('/film-stats/')
        .then(response => response.json())
        .then(data => {
            document.getElementById('film-count').textContent = `${thousands(data.film_count)} (${convertFramesToTime(data.film_dur)})`;
        });

    fetch('/season-stats/')
        .then(response => response.json())
        .then(data => {
            document.getElementById('season-count').textContent = `${thousands(data.season_count)} (${convertFramesToTime(data.season_dur)})`;
        });
});

document.addEventListener('DOMContentLoaded', function() {
    fetch(`/load_pool_table/`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('pool-table-container').innerHTML = data.html;
            updateMainProgramId();
            fastSearch(document.getElementById('search_input'));
        })
        .catch(error => {
            document.getElementById('pool-table-container').innerHTML = `
                <div class="alert alert-danger">Ошибка загрузки данных</div>
            `;
    });
});


document.getElementById('search_input').addEventListener('keyup', function(event) {
    fastSearch(event.target);
});

function fastSearch(searchInput) {
    let filter = searchInput.value.toLowerCase();
    let tableBody = document.getElementById('tableBody');
    let rows = tableBody.getElementsByTagName('tr');
    let searchSettings = Number(document.getElementById('search_type').value)+1;

    for (let i = 0; i < rows.length; i++) {
        let nameCell = rows[i].getElementsByTagName('td')[searchSettings];
        if (nameCell) {
            let textValue = nameCell.textContent || nameCell.innerText;
            rows[i].style.display = textValue.toLowerCase().indexOf(filter) > -1 ? '' : 'none';
        }
    }
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

function showApproveCommonTask() {
    let program_id_check_list = document.getElementsByName('program_id_check');
    let checked_list = [];
    let program_name_check_list = [];
    for (let i = 0; i < program_id_check_list.length; i++) {
        if (program_id_check_list[i].checked) {
            checked_list.push(program_id_check_list[i].value);
            let programName = program_id_check_list[i].dataset.programName;
                if (program_id_check_list[i].dataset.productionYear) {
                    programName += ` (${program_id_check_list[i].dataset.productionYear})`;
                }
            program_name_check_list.push(programName);
        }
    }
    if (checked_list.length > 0) {
        const ApproveCommonTask = new bootstrap.Modal(document.getElementById('ApproveCommonTask'));
        let program_name_list = document.getElementById('program_name_list');
        let dateInput = document.getElementById('work_date');
        program_name_list.innerHTML = ''
        dateInput.value = ''
        for (let i = 0; i < program_name_check_list.length; i++) {
            let list_item = document.createElement("li");
            list_item.classList.add('list-group-item');
            list_item.classList.add('list-group-item-action');
            list_item.textContent = program_name_check_list[i];
            program_name_list.appendChild(list_item);
        }
        ApproveCommonTask.toggle();
    }
    else {
        console.log('error');
        const errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
        error_message = document.getElementById('error_message');
        error_message.textContent = 'Ни одна задача не выбрана!'
        errorModal.toggle();
    }
};

function addInCommonTask() {
    let program_id_check_list = document.getElementsByName('program_id_check');
    let checked_list = [];
    for (let i = 0; i < program_id_check_list.length; i++) {
        if (program_id_check_list[i].checked) {
            checked_list.push(program_id_check_list[i].value)
        }
    };
    let work_date = document.getElementById('work_date').value;
    fetch('add_in_common_task/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify([checked_list, work_date]),
        credentials: 'same-origin'
    })
    .then(response => {
        if (!response.ok) {
             console.error(response.status);
        }
        return response.json();
    })
    .then(data => {
        if (data.status !== 'success') {
            console.error(data.message || 'Unknown server error');
            const errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
            error_message = document.getElementById('error_message');
            error_message.textContent = data.message
            const ApproveCommonTask = bootstrap.Modal.getInstance(document.getElementById('ApproveCommonTask')) ||
             new bootstrap.Modal(document.getElementById('ApproveCommonTask'));
            ApproveCommonTask.hide();
            errorModal.toggle();
        }
        else {
            window.location.href = '/common_pool/';
        }
    })
    .catch(error => {
        console.error('Error:', error);

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

function ValidateForm() {
    let dateInput = document.getElementById('work_date');
    if (!dateInput.value) {
          dateInput.classList.add('is-invalid');
          return;
    }
    dateInput.classList.remove('is-invalid');
    addInCommonTask();

}
