function showNotification() {
    fetch('/notifications/notification_create/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify([1]),
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            console.log(data.status, data.message);
        }
        else {
            console.log('error', data.message);
        }
    })
    .catch(error => {
        console.error('Error sending info:', error);
    });
}

document.addEventListener('DOMContentLoaded', function() {
    try {
        loadNotificationList();
    } catch(error) {
        console.error('Error sending info:', error);
    }

    try {
        let editorsNotificationFilters = document.querySelectorAll('.editors_notification_filter');
        editorsNotificationFilters.forEach(NotificationFilter => {
            NotificationFilter.addEventListener('change', function (e) {
                updateEditorsNotificationFilter(e.target);
            });
        })
    } catch(error) {
        console.error('Error updating filter:', error);
    }

    try {
        let searchInput = document.getElementById('search_input');
        searchInput.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                loadNotificationList();
            }
        })
    } catch(error) {
        console.error('Error setup event:', error);
    }

});

function initTableCheckboxes() {
    try {
        let notificationsTable = document.getElementById('notifications_table');
        let tableCheckboxes = notificationsTable.querySelectorAll('.notification-checkbox');
        tableCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', changeMainCheckbox)
        })
    } catch(error) {
        console.error('Error setup event:', error);
    }
}

function loadNotificationList(page_number=null) {
    let editorsListContainer = document.getElementById('editors_list_container');
    let searchInput = document.getElementById('search_input');

    if (!page_number) {
        let currentPage = document.querySelector('.pagination .page-item.active');
        page_number = currentPage?.dataset?.pageNumber || 1;
    }

    editorsListContainer.innerHTML = `
        <div class="text-center py-5">
          <div class="spinner-border text-primary" style="width: 3rem; height: 3rem;" role="status">
            <span class="visually-hidden">Загрузка данных...</span>
          </div>
          <p class="mt-3">Идет загрузка таблицы...</p>
        </div>
    `;
    fetch('/playlist/load_notification_list/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
            search_input: searchInput.value,
            page_number: page_number
        }),
        credentials: 'same-origin'
    })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                editorsListContainer.innerHTML = data.html;
                initTableCheckboxes()

            } else {
                editorsListContainer.innerHTML = `<div class="alert alert-danger">Ошибка загрузки данных</div>`;
                console.error('Error:', data.message);
            }
        })
        .catch(error => {
            console.error('Error loading notification list:', error);
        });
}

function switchPageNumber(pageNumber) {
    try {
        loadNotificationList(pageNumber.dataset?.pageNumber || 1)
    } catch(error) {
        console.error('Error switching page:', error);
    }

}

function updateEditorsNotificationFilter(filter_field) {

    fetch('/playlist/update_editors_notification_filter/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
            filter_key: filter_field.id,
            filter_value: filter_field.value
        }),
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            console.log(data.status, data.message);
            loadNotificationList();

        }
        else {
            console.log('error', data.message);
        }
    })
    .catch(error => {
        console.error('Error sending info:', error);
    });
}


function changeTableCheckboxes() {
    let mainCheckbox = document.getElementById('main_notification_checkbox');
    let notificationsTable = document.getElementById('notifications_table');
    let tableCheckboxes = notificationsTable.querySelectorAll('.notification-checkbox');

    tableCheckboxes.forEach(checkbox => {
        if (!mainCheckbox.indeterminate) {
            checkbox.checked = mainCheckbox.checked;
        }
        else {
            checkbox.checked = !mainCheckbox.checked
        }
    })
};

function changeMainCheckbox() {
    let mainCheckbox = document.getElementById('main_notification_checkbox');
    let notificationsTable = document.getElementById('notifications_table');
    let tableCheckboxes = notificationsTable.querySelectorAll('.notification-checkbox');
    let checkedCheckboxesList = []

    tableCheckboxes.forEach(checkbox => {
        if (checkbox.checked) {
        checkedCheckboxesList.push(checkbox);
    }
    });
    if (0 < checkedCheckboxesList.length && checkedCheckboxesList.length < tableCheckboxes.length) {
        mainCheckbox.indeterminate = true;
        mainCheckbox.checked = false;
    }
    else if (checkedCheckboxesList.length === tableCheckboxes.length) {
        mainCheckbox.indeterminate = false;
        mainCheckbox.checked = true;
    }
    else if (checkedCheckboxesList.length === 0) {
        mainCheckbox.indeterminate = false;
        mainCheckbox.checked = false;
    }
}

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