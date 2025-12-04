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
        $(this).val(picker.startDate.format('DD.MM.YYYY') + ' - ' + picker.endDate.format('DD.MM.YYYY'));

        // Загружаем данные после выбора даты
        load_schedule_table();
    });

    $('input[name="schedule_date"]').on('cancel.daterangepicker', function(ev, picker) {
        $(this).val('');
        // Загружаем данные при очистке
        load_schedule_table();
    });

    // Также слушаем обычное change на случай ручного ввода
    $('input[name="schedule_date"]').on('change', function() {
        setTimeout(load_schedule_table, 300); // Небольшая задержка
    });
});