$(function() {
    // Инициализация daterangepicker
    $('input[name="schedule_date"]').daterangepicker({
        "showWeekNumbers": true,
        "autoApply": true,
        "locale": {
            "format": "DD.MM.YYYY",
            "separator": " - ",
            "applyLabel": "Выбрать",
            "cancelLabel": "Отмена",
            "fromLabel": "От",
            "toLabel": "До",
            "customRangeLabel": "Другое",
            "weekLabel": "Н",
            "daysOfWeek": [
                "Вс",
                "Пн",
                "Вт",
                "Ср",
                "Чт",
                "Пт",
                "Сб"
            ],
            "monthNames": [
                "Январь",
                "Февраль",
                "Март",
                "Апрель",
                "Май",
                "Июнь",
                "Июль",
                "Август",
                "Сентябрь",
                "Октябрь",
                "Ноябрь",
                "Декабрь"
            ],
            "firstDay": 1
        },
    });

    // Слушаем событие apply.daterangepicker
    $('input[name="schedule_date"]').on('apply.daterangepicker', function(ev, picker) {
        let dateString = picker.startDate.format('DD.MM.YYYY') + ' - ' + picker.endDate.format('DD.MM.YYYY');
        $(this).val(dateString);

        updateScheduleFilter({ scheduleDate: dateString });

        // Загружаем данные после выбора даты
        load_schedule_table({ scheduleDate: dateString });
    });

    $('input[name="schedule_date"]').on('cancel.daterangepicker', function(ev, picker) {
        $(this).val('');
        // Загружаем данные при очистке
        updateScheduleFilter({ scheduleDate: '' });
        load_schedule_table({ scheduleDate: '' });
    });

});

document.addEventListener('DOMContentLoaded', function() {
    load_schedule_table();

    let scheduleDate = document.getElementById('schedule_date');
    if (scheduleDate) {
        scheduleDate.addEventListener('change', function(event) {
    load_schedule_table({ scheduleDate: this.value }); // или event.target.value
});
    }
});

function load_schedule_table(options = {}) {
     const {
        scheduleDate = document.getElementById('schedule_date')?.value || '',
        scheduleId = document.getElementById('current_schedule')?.dataset.currentScheduleId || null,
    } = options;
    console.log(scheduleDate, scheduleId);
    let scheduleTable = document.getElementById('schedule_table_container');
    if (scheduleTable) {
        scheduleTable.innerHTML = `
        <div class="text-center py-5">
            <div class="spinner-border text-primary" style="width: 3rem; height: 3rem;" role="status">
                <span class="visually-hidden">Загрузка данных...</span>
            </div>
            <p class="mt-3">Идет загрузка таблицы...</p>
        </div>
    `;
    }

    fetch('/playlist/load_schedule_table/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
            schedule_date: scheduleDate,
            schedule_id: scheduleId,
        }),
        credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(data => {
            if (scheduleTable) {
                scheduleTable.innerHTML = data.html;
                console.log('Таблица загружена, вызываем инициализацию...');

                // // ВАЖНО: Вызываем инициализацию после загрузки
                // if (typeof window.scheduleDay !== 'undefined' &&
                //     typeof window.scheduleDay.initScheduleDay === 'function') {
                //     // Даем время на рендеринг DOM
                //     setTimeout(() => {
                //         window.scheduleDay.initScheduleDay();
                //     }, 50);
                // } else {
                //     console.error('Функция initScheduleDay не найдена!');
                // }
            }
        })
        .catch(error => {
            console.log(document.getElementById('schedule_table_container'));
            document.getElementById('schedule_table_container').innerHTML = `
                <div class="alert alert-danger">Ошибка загрузки данных</div>
            `;
    });
};

function updateScheduleFilter(options = {}) {
    const {
        scheduleDate = document.getElementById('schedule_date')?.value || '',
        scheduleId = document.getElementById('current_schedule')?.dataset?.currentScheduleId ?? null,
    } = options;

    fetch('/playlist/update_schedule_filter/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
            schedule_date: scheduleDate,
            schedule_id: scheduleId,
        }),
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status !== 'success') {
            console.log('error', data.message);
        }
    })
    .catch(error => {
        console.error('Error sending info:', error);
    });
};

function getScheduleInfo(schedule_id) {
        fetch('/playlist/get_schedule_info/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify(schedule_id),
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status !== 'success') {
            console.log('error', data.message);
            return
        }
        updateScheduleList(data?.schedule_info)
    })
    .catch(error => {
        console.error('Error sending info:', error);
    });
}

function getEditorInfo(editor_id) {

}

function updateScheduleList(scheduleInfo) {
    let currentSchedule = document.getElementById('current_schedule');
    let currentEditor = document.getElementById('current_editor');
    let scheduleImage = document.getElementById('schedule_image');
    let scheduleImageName = scheduleInfo?.image_name ?? null;
    let scheduleId = scheduleInfo.schedule_id;
    let scheduleName = scheduleInfo.schedule_name;
    if (currentSchedule && currentEditor && scheduleImage) {
        currentSchedule.textContent = scheduleName;
        currentEditor.textContent = scheduleInfo.editor_name;
        if (scheduleImageName) {
            scheduleImage.src = `/static/img/schedule_logo/${scheduleImageName}.png`;
        }
        else {
            scheduleImage.src = '/static/img/schedule_logo/base.png';
        }
    };
    updateScheduleFilter({ scheduleId: scheduleId });
    load_schedule_table({ scheduleId: scheduleId });
};

function formatDateToString(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}


// Функция получения относительных дат
function getRelativeDate(currentDateString, direction) {
    const date = new Date(currentDateString);

    if (direction === 'prev') {
        date.setDate(date.getDate() - 1);
    } else if (direction === 'next') {
        date.setDate(date.getDate() + 1);
    }

    return formatDateToString(date);
}

// Основная функция открытия модального окна
function openSchedDayListById(schedule) {
    let scheduleDayId = schedule.dataset.scheduleDayId;
    let scheduleId = schedule.dataset.scheduleId;
    let scheduleDayDate = schedule?.dataset?.scheduleDayDate;

    console.log('Opening schedule day by ID:', scheduleDayId);

    // Инициализация модального окна
    const scheduleDayModal = bootstrap.Modal.getInstance(document.getElementById('schedule_day_modal')) ||
                            new bootstrap.Modal(document.getElementById('schedule_day_modal'));

    const scheduleDayName = document.getElementById('schedule_day_name');
    const scheduleDayModalBody = document.getElementById('schedule_day_modal_body');

    // Устанавливаем заголовок и scheduleId
    scheduleDayName.textContent = schedule?.dataset.scheduleName || '';
    scheduleDayName.dataset.scheduleId = scheduleId || '';

    // Устанавливаем текущую дату в input
    const currentDateInput = document.getElementById('current_schedule_day_date');
    if (currentDateInput && scheduleDayDate) {
        currentDateInput.value = scheduleDayDate;
        currentDateInput.dataset.currentScheduleDayDate = scheduleDayDate;
    }

    // Показываем спиннер загрузки
    scheduleDayModalBody.innerHTML = `
    <div class="text-center py-5">
        <div class="spinner-border text-primary" style="width: 3rem; height: 3rem;" role="status">
            <span class="visually-hidden">Загрузка данных...</span>
        </div>
        <p class="mt-3">Идет загрузка таблицы...</p>
    </div>`;

    // Открываем модальное окно
    scheduleDayModal.show();

    // Загружаем данные
    fetch('/playlist/get_schedule_list_by_id/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify(scheduleDayId),
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            scheduleDayModalBody.innerHTML = data.html;
            console.log('Модальная таблица загружена по ID');
        } else {
            console.log('error', data.message);
            scheduleDayModalBody.innerHTML = `
                <div class="alert alert-danger">
                    Ошибка загрузки: ${data.message}
                </div>`;
        }
    })
    .catch(error => {
        console.error('Error sending info:', error);
        scheduleDayModalBody.innerHTML = `
            <div class="alert alert-danger">
                Ошибка соединения с сервером
            </div>`;
    });
}

// Функция загрузки по дате
function openSchedDayListByDate(scheduleDayDate) {
    const scheduleDayName = document.getElementById('schedule_day_name');
    const scheduleId = scheduleDayName?.dataset?.scheduleId;
    const scheduleDayModalBody = document.getElementById('schedule_day_modal_body');

    console.log('Loading schedule by date:', scheduleId, scheduleDayDate);

    // Обновляем текущую дату в input
    const currentDateInput = document.getElementById('current_schedule_day_date');
    if (currentDateInput) {
        currentDateInput.value = scheduleDayDate;
        currentDateInput.dataset.currentScheduleDayDate = scheduleDayDate;
    }

    // Показываем спиннер загрузки
    scheduleDayModalBody.innerHTML = `
    <div class="text-center py-5">
        <div class="spinner-border text-primary" style="width: 3rem; height: 3rem;" role="status">
            <span class="visually-hidden">Загрузка данных...</span>
        </div>
        <p class="mt-3">Идет загрузка таблицы...</p>
    </div>`;

    // Загружаем данные
    fetch('/playlist/get_schedule_list_by_date/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
            'schedule_id': scheduleId,
            'schedule_day_date': scheduleDayDate
        }),
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            scheduleDayModalBody.innerHTML = data.html;
            console.log('Модальная таблица загружена по дате');
        } else {
            console.log('error', data.message);
            scheduleDayModalBody.innerHTML = `
                <div class="alert alert-danger">
                    Ошибка загрузки: ${data.message}
                </div>`;
        }
    })
    .catch(error => {
        console.error('Error sending info:', error);
        scheduleDayModalBody.innerHTML = `
            <div class="alert alert-danger">
                Ошибка соединения с сервером
            </div>`;
    });
}

// Функция навигации по датам
function handleDateNavigation(action) {
    const currentDateInput = document.getElementById('current_schedule_day_date');
    if (!currentDateInput || !currentDateInput.value) return;

    const currentDate = currentDateInput.value;
    const newDate = getRelativeDate(currentDate, action);

    // Обновляем input
    currentDateInput.value = newDate;
    currentDateInput.dataset.currentScheduleDayDate = newDate;

    // Загружаем данные для новой даты
    openSchedDayListByDate(newDate);
}

// Функция для обработки ручного ввода даты
function handleManualDateChange() {
    const currentDateInput = document.getElementById('current_schedule_day_date');
    if (!currentDateInput || !currentDateInput.value) return;

    const newDate = currentDateInput.value;
    currentDateInput.dataset.currentScheduleDayDate = newDate;

    // Загружаем данные для новой даты
    openSchedDayListByDate(newDate);
}

// Инициализация обработчиков событий
function initDateNavigation() {
    // Обработчики для кнопок навигации
    const prevBtn = document.getElementById('prev_date');
    const nextBtn = document.getElementById('next_date');
    const dateInput = document.getElementById('current_schedule_day_date');

    if (prevBtn) {
        prevBtn.addEventListener('click', function(e) {
            e.preventDefault();
            handleDateNavigation('prev');
        });
    }

    if (nextBtn) {
        nextBtn.addEventListener('click', function(e) {
            e.preventDefault();
            handleDateNavigation('next');
        });
    }

    if (dateInput) {
        // Обработчик изменения через клавишу Enter
        dateInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                handleManualDateChange();
            }
        });

        // Обработчик изменения даты (для браузеров с datepicker)
        dateInput.addEventListener('change', function() {
            handleManualDateChange();
        });
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    initDateNavigation();
});

function updateStatus(statusInfo) {
    console.log(statusInfo.dataset.scheduleDayId);
    console.log(statusInfo.value);
};

function updateComment() {

};

function updatePlaylistInfo() {
    console.log('Отправка данных:', data);

    fetch('/playlist/update_playlist_info/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            console.log('Обновлено успешно');
        }
    })
    .catch(error => {
        console.error('Ошибка:', error);
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