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

                // ВАЖНО: Вызываем инициализацию после загрузки
                if (typeof window.scheduleDay !== 'undefined' &&
                    typeof window.scheduleDay.initScheduleDay === 'function') {
                    // Даем время на рендеринг DOM
                    setTimeout(() => {
                        window.scheduleDay.initScheduleDay();
                    }, 50);
                } else {
                    console.error('Функция initScheduleDay не найдена!');
                }
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

function updateScheduleTable(schedule) {
    let currentSchedule = document.getElementById('current_schedule');
    let currentScheduleId = schedule?.dataset?.scheduleId ?? null;
    let currentEditor = document.getElementById('current_editor');
    let currentScheduleDescription = document.getElementById('current_schedule_description');
    if (currentSchedule && currentEditor && currentScheduleDescription) {
        currentSchedule.textContent = schedule.dataset.scheduleName;
        currentSchedule.dataset.currentScheduleId = currentScheduleId;
        currentEditor.textContent = schedule.dataset.editorName;
        currentScheduleDescription.textContent = schedule.dataset.description;
    };
    updateScheduleFilter({ scheduleId: currentScheduleId });
    load_schedule_table({ scheduleId: currentScheduleId });
};

function openSchedDayTable(schedule) {
    let scheduleDayId = schedule.dataset.scheduleDayId;
    console.log(scheduleDayId);
    const scheduleDayModal = bootstrap.Modal.getInstance(document.getElementById('schedule_day_modal')) ||
                            new bootstrap.Modal(document.getElementById('schedule_day_modal'));
    let scheduleDayModalBody = document.getElementById('schedule_day_modal_body')


    fetch('/playlist/get_schedule_day_table/', {
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
            console.log('Модальная таблица загружена, инициализируем...');

            if (typeof window.scheduleDay !== 'undefined' &&
                typeof window.scheduleDay.initScheduleDay === 'function') {
                setTimeout(() => {
                    window.scheduleDay.initScheduleDay();
                }, 100);
            }
            scheduleDayModal.toggle()
        }
        else {
            console.log('error', data.message);
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