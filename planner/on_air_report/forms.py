from django import forms

from main.form_choices import choice
from on_air_report.models import OnAirModel, TaskSearch


class OnAirReportFilter(forms.ModelForm):
    class Meta:
        model = OnAirModel
        fields = ('sched_dates', 'workers', 'material_type', 'schedules', 'task_status', 'order_type', 'order')
        labels = {'sched_dates': 'Дата эфирной сетки', 'workers': 'Выполняет', 'material_type': 'Тип материала',
                  'schedules': 'Канал', 'task_status': 'Статус задачи'}

        widgets = {
            'ready_dates': forms.DateInput(
                attrs={'class': 'form-control', 'data-bs-theme': 'light', 'type': 'text', 'id': 'ready_dates'}),
            'sched_dates': forms.DateInput(
                attrs={'class': 'form-control', 'data-bs-theme': 'light', 'type': 'text', 'id': 'sched_dates'}),
            'workers': forms.SelectMultiple(
                attrs={'class': 'ui selection dropdown w-100', 'id': 'workers'},
                choices=choice.workers('Выполняет')),
            'material_type': forms.SelectMultiple(
                attrs={'class': 'ui selection dropdown w-100', 'id': 'material_type'},
                choices=choice.material_type('Тип материала')),
            'schedules': forms.SelectMultiple(
                attrs={'class': 'ui selection dropdown w-100', 'id': 'schedules'},
                choices=choice.schedules('Канал')),
            'task_status': forms.SelectMultiple(
                attrs={'class': 'ui selection dropdown w-100', 'id': 'task_status'},
                choices=choice.task_status(label='Статус', extra=('oplan_ready', 'Отсмотрен в Oplan3'))),
            'order_type': forms.TextInput(
                attrs={
                    'class': 'visually-hidden', 'id': 'order_type',
                    },
            ),
            'order': forms.TextInput(
                attrs={
                    'class': 'visually-hidden', 'id': 'order',
                    },
            ),
        }

class TaskSearchForm(forms.ModelForm):
    class Meta:
        model = TaskSearch
        fields = ('search_type', 'search_input', 'sql_set')

        labels = {'search_type': '', 'search_input': '', 'sql_set': 'Показать'}

        widgets = {
            'search_type': forms.Select(
                attrs={'class': 'form-select', 'id': 'search_type', 'style': 'min-width: 10rem; max-width: 10rem;'},
                choices=((0, 'program id'), (1, 'clip id'), (2, 'названию'), (3, 'имени файла'))),
            'search_input': forms.TextInput(
                attrs={
                    'class': 'form-control', 'id': 'search_input', 'placeholder': 'введите название передачи ...',
                    'autocomplete': "off", 'autocorrect': "off", 'spellcheck': "false"},
            ),
            'sql_set': forms.Select(
                attrs={'class': 'form-select', 'id': 'sql_set', 'style': 'max-width: 11rem;'},
                choices=choice.sql_set()),
        }

class OnAirCalendar(forms.Form):
    month_dropdown = forms.ChoiceField(widget=forms.Select(
        attrs={'class': "form-select", 'id': "month_dropdown", 'onchange': "this.form.submit()"}),
        label='месяц', choices=choice.months, required=True)

    year_dropdown = forms.ChoiceField(widget=forms.Select(
        attrs={'class': "form-select", 'id': "year_dropdown", 'onchange': "this.form.submit()"}),
        label='год', choices=choice.years, required=True)

    channel_dropdown = forms.ChoiceField(widget=forms.Select(
        attrs={'class': "form-select", 'id': "channel_dropdown", 'onchange': "this.form.submit()"}),
        label='каналы', choices=choice.channels, required=False)