from django import forms

from main.form_choices import Choices
from on_air_report.models import OnAirModel, TaskSearch

choice = Choices()


class OnAirReportFilter(forms.ModelForm):
    class Meta:
        model = OnAirModel
        fields = ('sched_dates', 'workers', 'material_type', 'schedules', 'task_status')

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
        }

class TaskSearchForm(forms.ModelForm):
    class Meta:
        model = TaskSearch
        fields = ('search_type', 'search_input', 'sql_set')

        labels = {'search_type': '', 'search_input': '', 'sql_set': 'Показать'}

        widgets = {
            'search_type': forms.Select(
                attrs={'class': 'form-select', 'id': 'search_type', 'style': 'max-width: 10rem;'},
                choices=((0, 'id'), (1, 'названию'), (2, 'имени файла'))),
            'search_input': forms.TextInput(
                attrs={
                    'class': 'form-control', 'id': 'search_input', 'placeholder': 'введите название передачи ...',
                    'autocomplete': "off", 'data-bs-toggle': "dropdown", 'data-bs-auto-close': "false",
                    'data-bs-offset': "0,12", 'aria-expanded': "false", 'aria-haspopup': "true",
                    'aria-controls': "on_air_search_filter"
                },
            ),
            'sql_set': forms.Select(
                attrs={'class': 'form-select', 'id': 'sql_set', 'style': 'max-width: 11rem;'},
                choices=choice.sql_set()),
        }