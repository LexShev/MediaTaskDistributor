$.fn.dropdown.settings.message = {
  addResult     : 'Add <b>{term}</b>',
  count         : '{count} выбрано',
  maxSelections : 'Max {maxCount} selections',
  noResults     : 'No results found.',
  serverError   : 'There was an error contacting the server'
};

$(function() {
  $('.ui.dropdown').dropdown();
});

$('#schedules')
  .dropdown()
;
$('#workers')
  .dropdown()
;

$('#material_type')
  .dropdown(
  {
    useLabels: true
  }
  )
;

$('#task_status')
  .dropdown()
;

$(function() {

  $('input[name="ready_dates"]').daterangepicker({
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

  $('input[name="ready_dates"]').on('apply.daterangepicker', function(ev, picker) {
      $(this).val(picker.startDate.format('DD.MM.YYYY') + ' - ' + picker.endDate.format('DD.MM.YYYY'));
  });

  $('input[name="ready_dates"]').on('cancel.daterangepicker', function(ev, picker) {
      $(this).val('');
  });

});

$(function() {

  $('input[name="sched_dates"]').daterangepicker({
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

  $('input[name="sched_dates"]').on('apply.daterangepicker', function(ev, picker) {
      $(this).val(picker.startDate.format('DD.MM.YYYY') + ' - ' + picker.endDate.format('DD.MM.YYYY'));
  });

  $('input[name="sched_dates"]').on('cancel.daterangepicker', function(ev, picker) {
      $(this).val('');
  });

});