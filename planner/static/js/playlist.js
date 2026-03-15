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

        updateScheduleFilter({ 'schedule_date': dateString });
        // Загружаем данные после выбора даты
    });

    // $('input[name="schedule_date"]').on('cancel.daterangepicker', function(ev, picker) {
    //     $(this).val('');
    //     // Загружаем данные при очистке
    //     updateScheduleFilter({ 'schedule_date': '' });
    //     load_schedule_table({ scheduleDate: '' });
    // });

});

document.addEventListener('DOMContentLoaded', function() {
    load_schedule_table();

    let inputScheduleDate = document.getElementById('schedule_date');
    if (inputScheduleDate) {
        inputScheduleDate.addEventListener('change', function(event) {
            updateScheduleFilter({ 'schedule_date': event.target.value });
        });
    }
    try {
        initPlaylistSettings();
    }
    catch(e) {
        console.error('Ошибка при инициализации:',e);
    }

});

function initPlaylistSettings() {
    ['channels-collapse', 'editors-collapse', 'stats-collapse'].forEach(id => {
        const el = document.getElementById(id);

        el.addEventListener('shown.bs.collapse', () => {
            localStorage.setItem(id, 'show');
        });

        el.addEventListener('hidden.bs.collapse', () => {
            localStorage.setItem(id, '');
        });

        if (localStorage.getItem(id)) el.classList.add('show');
    });
}

function load_schedule_table() {
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

    fetch('/playlist/load_schedule_table/')
        .then(response => response.json())
        .then(data => {
            if (scheduleTable) {
                scheduleTable.innerHTML = data.html;
                updateScheduleInfo(data.scheduleInfo)
                console.log('Таблица загружена');
            }
        })
        .catch(error => {
            console.log(error);
            document.getElementById('schedule_table_container').innerHTML = `
                <div class="alert alert-danger">Ошибка загрузки данных</div>
            `;
    });
};

function updateScheduleFilter(filterFields) {

    fetch('/playlist/update_schedule_filter/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify(filterFields),
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            load_schedule_table();
        }
        else {
            console.log('error', data.message);
        }
    })
    .catch(error => {
        console.error('Error sending info:', error);
    });
};

function chooseSchedule(scheduleInfo) {
    let scheduleId = scheduleInfo.dataset.scheduleId;
    updateScheduleFilter({ 'schedule_id': scheduleId });
}

function chooseEditor(editorInfo) {
    let schedulesList = editorInfo.dataset.schedulesList;
    updateScheduleFilter({ 'schedule_id': schedulesList });

}

function updateScheduleInfo(scheduleInfoList) {
    let currentSchedule = document.getElementById('current_schedule');
    let currentEditor = document.getElementById('current_editor');
    let scheduleImage = document.getElementById('schedule_image');

    // Проверяем, что элементы существуют
    if (!currentSchedule || !currentEditor || !scheduleImage) {
        console.error('Элементы интерфейса не найдены');
        return;
    }

    // Убеждаемся, что работаем с массивом
    const schedules = Array.isArray(scheduleInfoList) ? scheduleInfoList : [scheduleInfoList];

    if (schedules.length === 0) {
        // Пустой список - сбрасываем интерфейс
        currentSchedule.textContent = 'Все каналы';
        currentEditor.textContent = 'Редакторы';
        scheduleImage.src = '/static/img/schedule_logo/base.png';
        // Очищаем dataset
        delete scheduleImage.dataset.scheduleId;
        return;
    }

    // Формируем список названий каналов
    const scheduleNames = schedules.map(s => s.schedule_name).filter(name => name);
    currentSchedule.textContent = scheduleNames.join(', ');

    // Формируем список ID каналов
    const scheduleIds = schedules.map(s => s.schedule_id).filter(id => id != null);
    if (scheduleIds.length > 0) {
        scheduleImage.dataset.scheduleId = JSON.stringify(scheduleIds);
    } else {
        delete scheduleImage.dataset.scheduleId;
    }

    // Отображаем редакторов
    const editorNames = schedules.map(s => s.editor_name).filter(name => name);
    if (editorNames.length > 0) {
        currentEditor.textContent = editorNames[0];
    } else {
        currentEditor.textContent = 'Редакторы';
    }

    // Для нескольких каналов всегда показываем базовую картинку
    if (schedules.length === 1 && schedules[0]?.image_name) {
        // Один канал - показываем его логотип
        scheduleImage.src = `/static/img/schedule_logo/${schedules[0].image_name}.png`;
    } else {
        // Несколько каналов или нет логотипа - показываем базовый
        scheduleImage.src = '/static/img/schedule_logo/base.png';
    }
}

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

    // Устанавливаем заголовок и scheduleId
    scheduleDayName.textContent = schedule?.dataset.scheduleName || '';
    scheduleDayName.dataset.scheduleId = scheduleId || '';

    // Устанавливаем текущую дату в input
    const currentDateInput = document.getElementById('current_schedule_day_date');
    if (currentDateInput && scheduleDayDate) {
        currentDateInput.value = scheduleDayDate;
        currentDateInput.dataset.currentScheduleDayDate = scheduleDayDate;
    }

    // Открываем модальное окно
    scheduleDayModal.show();

    let query = JSON.stringify({'schedule_day_id': scheduleDayId})
    getScheduleList(query)

}

// Функция загрузки по дате
function openSchedDayListByDate(scheduleDayDate) {
    const scheduleDayName = document.getElementById('schedule_day_name');
    const scheduleId = scheduleDayName?.dataset?.scheduleId;

    console.log('Loading schedule by date:', scheduleId, scheduleDayDate);

    // Обновляем текущую дату в input
    const currentDateInput = document.getElementById('current_schedule_day_date');
    if (currentDateInput) {
        currentDateInput.value = scheduleDayDate;
        currentDateInput.dataset.currentScheduleDayDate = scheduleDayDate;
    }

    let query = JSON.stringify({
            'schedule_id': scheduleId,
            'schedule_day_date': scheduleDayDate
        })
    getScheduleList(query)
}

function getScheduleList(query) {
    const scheduleDayModalBody = document.getElementById('schedule_day_modal_body');

    // Показываем спиннер загрузки
    scheduleDayModalBody.innerHTML = `
    <div class="text-center py-5">
        <div class="spinner-border text-primary" style="width: 3rem; height: 3rem;" role="status">
            <span class="visually-hidden">Загрузка данных...</span>
        </div>
        <p class="mt-3">Идет загрузка таблицы...</p>
    </div>`;

    fetch('/playlist/get_schedule_list/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: query,
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

function updatePlaylistStatus(statusInfo) {
    const scheduleDayId = statusInfo.parentElement?.dataset?.scheduleDayId || null;
    const status = statusInfo.value || null;

    console.log('Отправка данных:', {
            'schedule_day_id': scheduleDayId,
            'status': status,
        });

    fetch('/playlist/update_playlist_status/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
            'schedule_day_id': scheduleDayId,
            'status': status,
        })
    })
    .then(response => response.json())
    .then(result => {
        if (result.status === 'success') {
            console.log('Обновлено успешно');
        }
        else {
            console.error(result.message)
        }
    })
    .catch(error => {
        console.error('Ошибка:', error);
    });
};

let currentCommentInput = null;
let isSwitchingInput = false;

function startCommentEditing(input) {

    // Завершаем редактирование предыдущего поля, если оно было
    if (currentCommentInput && currentCommentInput !== input) {
        isSwitchingInput = true;
        finishCommentEditing(currentCommentInput);
    }

    currentCommentInput = input;

    // Сохраняем начальное значение
    input._initialValue = input.value;

    const handleOutsideClick = (e) => {
        const isOtherInput = e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA';

        if (!input.contains(e.target)) {
            // Если кликнули на другой инпут
            if (isOtherInput) {
                // Просто завершаем редактирование (сохранение произойдет в startCommentEditing нового инпута)
                cancelCommentEditing(input);
            } else {
                // Если кликнули не на инпут - проверяем изменения
                if (input._initialValue !== input.value) {
                    finishCommentEditing(input);
                } else {
                    cancelCommentEditing(input);
                }
            }
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (input._initialValue !== input.value) {
                finishCommentEditing(input);
            } else {
                cancelCommentEditing(input);
            }
        }
    };

    // Убираем предыдущие обработчики, если они были
    if (input._editHandlers) {
        document.removeEventListener('click', input._editHandlers.handleOutsideClick);
        input.removeEventListener('keydown', input._editHandlers.handleKeyDown);
    }

    // Добавляем новые обработчики
    document.addEventListener('click', handleOutsideClick);
    input.addEventListener('keydown', handleKeyDown);

    // Сохраняем ссылки на обработчики
    input._editHandlers = { handleOutsideClick, handleKeyDown };
}

function cancelCommentEditing(input) {
    if (!input) return;

    // Очищаем обработчики
    if (input._editHandlers) {
        document.removeEventListener('click', input._editHandlers.handleOutsideClick);
        input.removeEventListener('keydown', input._editHandlers.handleKeyDown);
        delete input._editHandlers;
    }

    if (currentCommentInput === input) {
        currentCommentInput = null;
    }

    input.blur();
    delete input._initialValue;

    setTimeout(() => {
        isSwitchingInput = false;
    }, 100);
}

function finishCommentEditing(input) {
    if (!input) return;

    // Проверяем, действительно ли значение изменилось
    if (input._initialValue !== input.value) {
        updatePlaylistComment(input);
    } else {
        cancelCommentEditing(input);
        return;
    }

    // Удаляем обработчики
    if (input._editHandlers) {
        document.removeEventListener('click', input._editHandlers.handleOutsideClick);
        input.removeEventListener('keydown', input._editHandlers.handleKeyDown);
        delete input._editHandlers;
    }

    if (currentCommentInput === input) {
        currentCommentInput = null;
    }

    input.blur();
    delete input._initialValue;
}

function showIndicator(input, status) {
    // Добавляем класс для отображения галочки
    input.classList.add(`border-${status}`);

    // Убираем галочку через 2 секунды
    setTimeout(() => {
        input.classList.remove(`border-${status}`);
    }, 1400);
}

function updatePlaylistComment(input) {
    const scheduleDayId = input.parentElement?.dataset?.scheduleDayId || null;
    const comment = input.value || '';

    console.log('Отправка данных:', {
            'schedule_day_id': scheduleDayId,
            'comment': comment,
        });

    fetch('/playlist/update_playlist_comment/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
            'schedule_day_id': scheduleDayId,
            'comment': comment,
        })
    })
    .then(response => response.json())
    .then(result => {
        if (result.status === 'success') {
            console.log('Обновлено успешно');
            showIndicator(input, 'success');
            // Обновляем начальное значение после успешного сохранения
            input._initialValue = input.value;
        }
        else {
            console.error(result.message)
            showIndicator(input, 'error');
        }
    })
    .catch(error => {
        console.error('Ошибка:', error);
        showIndicator(input, 'error');
    })
    .finally(() => {
        setTimeout(() => {
            isSwitchingInput = false;
        }, 100);
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