$('#schedules')
  .dropdown()
;
$('#workers')
  .dropdown()
;

$('#material_type')
  .dropdown()
;

$('#task_status')
  .dropdown()
;

$(function() {

  $('input[name="work_dates"]').daterangepicker({
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

  $('input[name="work_dates"]').on('apply.daterangepicker', function(ev, picker) {
      $(this).val(picker.startDate.format('DD.MM.YYYY') + ' - ' + picker.endDate.format('DD.MM.YYYY'));
  });

  $('input[name="work_dates"]').on('cancel.daterangepicker', function(ev, picker) {
      $(this).val('');
  });

});