document.addEventListener('DOMContentLoaded', function() {
    loadTable();
    document.getElementById('search_input').addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            applyFilters();
        }
    });
});

function loadTable(page) {
    page = page || 1;
    document.getElementById('admin_task_table').innerHTML =
        '<div class="text-center py-5">' +
            '<div class="spinner-border text-primary" style="width: 3rem; height: 3rem;" role="status">' +
                '<span class="visually-hidden">Загрузка данных...</span>' +
            '</div>' +
            '<p class="mt-3">Идет загрузка таблицы...</p>' +
        '</div>';

    return fetch('/task_manager/load_admin_task_table/?page=' + page)
        .then(response => response.json())
        .then(data => {
            document.getElementById('admin_task_table').innerHTML = data.html;
            document.getElementById('pagination_container').innerHTML = data.pagination || '';
            if (data.order) {
                document.getElementById('order').value = data.order;
            }
            if (data.order_type) {
                document.getElementById('order_type').value = data.order_type;
            }
            updateMainProgramId();
        })
        .catch(error => {
            document.getElementById('admin_task_table').innerHTML = `
                <div class="alert alert-danger">Ошибка загрузки данных</div>
            `;
        });
}

function applyFilters() {
    var filters = {};
    var filterFields = ['ready_date', 'sched_date', 'deadline', 'worker_id',
                        'material_type', 'sched_id', 'task_status', 'extra_set'];
    filterFields.forEach(function(id) {
        var el = document.getElementById(id);
        filters[id] = el ? el.value : '';
    });

    var search = {};
    var searchFields = ['search_type', 'search_input', 'sql_set'];
    searchFields.forEach(function(id) {
        var el = document.getElementById(id);
        search[id] = el ? el.value : '';
    });

    fetch('/task_manager/save_filters/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({filters: filters, search: search}),
        credentials: 'same-origin'
    })
    .then(function(response) { return response.json(); })
    .then(function(data) {
        if (data.status === 'success') {
            loadTable(1);
        }
    })
    .catch(function(error) {
        console.error('Error saving filters:', error);
    });
}

function resetFilters() {
    var filterFields = ['ready_date', 'sched_date', 'deadline', 'worker_id',
                        'material_type', 'sched_id', 'task_status', 'extra_set'];
    filterFields.forEach(function(id) {
        var el = document.getElementById(id);
        if (el) { el.value = ''; }
    });
    var searchInput = document.getElementById('search_input');
    if (searchInput) { searchInput.value = ''; }
    applyFilters();
}

function sortTable(element) {
    var order = element.dataset.order;
    var curOrderEl = document.getElementById('order');
    var curOrderTypeEl = document.getElementById('order_type');
    var curOrder = curOrderEl ? curOrderEl.value : '';
    var curOrderType = curOrderTypeEl ? curOrderTypeEl.value : 'ASC';

    if (order === curOrder) {
        curOrderType = (curOrderType === 'DESC') ? 'ASC' : 'DESC';
    } else {
        curOrderType = 'ASC';
    }

    fetch('/task_manager/sort_table/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify([order, curOrderType]),
        credentials: 'same-origin'
    })
    .then(function(response) { return response.json(); })
    .then(function(data) {
        if (data.status === 'success') {
            if (curOrderEl) { curOrderEl.value = order; }
            if (curOrderTypeEl) { curOrderTypeEl.value = curOrderType; }
            loadTable(1);
        }
    })
    .catch(function(error) {
        console.error('Error sorting:', error);
    });
}

function showApproveTaskChange() {
    var checked = getCheckedCheckboxes();
    if (checked.length === 0) {
        var errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
        errorModal.show();
        return;
    }
    var approveModal = new bootstrap.Modal(document.getElementById('ApproveTaskChange'));
    approveModal.show();
}

function batchAction() {
    var changeType = document.getElementById('change_type').value;
    var checkboxes = getCheckedCheckboxes();
    var checkedValues = checkboxes.map(function(cb) { return cb.value; });
    var allCheckboxes = document.getElementsByName('program_id_check');

    var payload = {
        change_type: changeType,
        program_id_check: checkedValues
    };

    if (changeType === '1') {
        var programIds = [];
        var engineers = [];
        var workDates = [];
        var statuses = [];
        var filePaths = [];
        for (var i = 0; i < allCheckboxes.length; i++) {
            var cb = allCheckboxes[i];
            var pid = cb.value;
            programIds.push(pid);

            var engEl = document.getElementById('workers_selector_' + pid);
            var wdEl = document.getElementById('work_date_selector_' + pid);
            var stEl = document.getElementById('status_selector_' + pid);
            var fpEl = document.getElementById('file_path_' + pid);

            engineers.push(engEl ? engEl.value : '');
            workDates.push(wdEl ? wdEl.value : '');
            statuses.push(stEl ? stEl.value : '');
            filePaths.push(fpEl ? fpEl.value : '');
        }
        payload.program_id = programIds;
        payload.engineers = engineers;
        payload.work_dates = workDates;
        payload.new_statuses = statuses;
        payload.file_paths = filePaths;
    } else if (changeType === '3') {
        var programIds = [];
        var workDates = [];
        for (var i = 0; i < allCheckboxes.length; i++) {
            var cb = allCheckboxes[i];
            var pid = cb.value;
            programIds.push(pid);
            var wdEl = document.getElementById('work_date_selector_' + pid);
            workDates.push(wdEl ? wdEl.value : '');
        }
        payload.program_id = programIds;
        payload.work_dates = workDates;
    }

    fetch('/task_manager/batch_action/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify(payload),
        credentials: 'same-origin'
    })
    .then(function(response) { return response.json(); })
    .then(function(data) {
        var approveModal = bootstrap.Modal.getInstance(document.getElementById('ApproveTaskChange'));
        if (approveModal) { approveModal.hide(); }

        if (data.status === 'success') {
            loadTable(1).then(function() {
                showMessage(data.message, 'success');
            });
        } else {
            showMessage(data.message, 'danger');
        }
    })
    .catch(function(error) {
        console.error('Error in batch action:', error);
        var approveModal = bootstrap.Modal.getInstance(document.getElementById('ApproveTaskChange'));
        if (approveModal) { approveModal.hide(); }
        showMessage('Ошибка при выполнении операции', 'danger');
    });
}

function showMessage(message, type) {
    var container = document.getElementById('message_container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'message_container';
        var table = document.getElementById('admin_task_table');
        if (table) { table.parentNode.insertBefore(container, table); }
    }
    var alert = document.createElement('div');
    alert.className = 'alert alert-' + type + ' alert-dismissible fade show';
    alert.role = 'alert';
    alert.innerHTML = message +
        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>';
    container.appendChild(alert);
    setTimeout(function() {
        if (alert.parentNode) { alert.remove(); }
    }, 5000);
}

function switchPageNumber(element) {
    var pageNum = element.dataset.pageNumber;
    if (pageNum) {
        loadTable(pageNum);
    }
}

function getCheckedCheckboxes() {
    var all = document.getElementsByName('program_id_check');
    var checked = [];
    for (var i = 0; i < all.length; i++) {
        if (all[i].checked) {
            checked.push(all[i]);
        }
    }
    return checked;
}

function changeProgramIdCheckbox() {
    var fullSelectCheckbox = document.getElementById('full_select');
    var tableBody = document.getElementById('tableBody');
    if (!tableBody) { return; }
    var visibleCheckboxes = tableBody.querySelectorAll('tr:not([style*="display: none"]) input[name="program_id_check"]');

    var checkedVisibleList = [];
    visibleCheckboxes.forEach(function(cb) {
        if (cb.checked) { checkedVisibleList.push(cb); }
    });

    if (checkedVisibleList.length > 0) {
        fullSelectCheckbox.indeterminate = false;
        fullSelectCheckbox.checked = false;
        visibleCheckboxes.forEach(function(cb) { cb.checked = false; });
    } else {
        fullSelectCheckbox.indeterminate = false;
        fullSelectCheckbox.checked = true;
        visibleCheckboxes.forEach(function(cb) { cb.checked = true; });
    }
}

function updateMainProgramId() {
    var fullSelectCheckbox = document.getElementById('full_select');
    var programIdCheckList = document.getElementsByName('program_id_check');

    function changeFullSelect() {
        var checkedList = [];
        for (var i = 0; i < programIdCheckList.length; i++) {
            if (programIdCheckList[i].checked) { checkedList.push(programIdCheckList[i]); }
        }
        if (checkedList.length > 0 && checkedList.length < programIdCheckList.length) {
            fullSelectCheckbox.indeterminate = true;
            fullSelectCheckbox.checked = false;
        } else if (checkedList.length === programIdCheckList.length) {
            fullSelectCheckbox.indeterminate = false;
            fullSelectCheckbox.checked = true;
        } else {
            fullSelectCheckbox.indeterminate = false;
            fullSelectCheckbox.checked = false;
        }
    }

    for (var i = 0; i < programIdCheckList.length; i++) {
        programIdCheckList[i].addEventListener('change', changeFullSelect);
    }
    if (fullSelectCheckbox) {
        fullSelectCheckbox.indeterminate = false;
        fullSelectCheckbox.checked = false;
    }
}

function adjustTextarea(dropdown) {
    var textareaList = dropdown.parentElement.getElementsByTagName('textarea');
    Array.from(textareaList).forEach(function(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = (textarea.scrollHeight + 10) + 'px';
    });
}

function convertFramesToTime(frames, fps) {
    fps = fps || 25;
    if (isNaN(frames) || frames === null || frames === undefined) { frames = 0; }
    var sec = parseInt(frames) / fps;
    var yy = Math.floor(Math.floor(sec / 3600 / 24) / 365);
    var dd = Math.floor(Math.floor(sec / 3600 / 24) % 365);
    var hh = Math.floor((sec / 3600) % 24);
    var mm = Math.floor((sec % 3600) / 60);
    var ss = Math.floor((sec % 3600) % 60);
    var ff = Math.floor((sec % 1) * fps);

    var formatNum = function(num) { return num.toString().padStart(2, '0'); };

    if (yy < 1) {
        if (dd < 1) {
            return formatNum(hh) + ':' + formatNum(mm) + ':' + formatNum(ss);
        } else {
            return formatNum(dd) + 'д. ' + formatNum(hh) + ':' + formatNum(mm) + ':' + formatNum(ss);
        }
    } else {
        var yearSuffix = (yy % 10 > 0 && yy % 10 < 5) ? 'г. ' : 'л. ';
        return formatNum(yy) + yearSuffix + formatNum(dd) + 'д. ' + formatNum(hh) + ':' + formatNum(mm) + ':' + formatNum(ss);
    }
}

function thousands(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
}

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
