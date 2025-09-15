from django import forms
from .models import AdminModel, TaskSearch
from main.form_choices import Choices


choice = Choices()

class AdminForm(forms.ModelForm):
    class Meta:
        model = AdminModel
        fields = ('ready_date', 'sched_date', 'deadline', 'worker_id', 'material_type', 'sched_id', 'task_status')
        labels = {'ready_date': 'Дата завершения',
                  'sched_date': 'Дата эфира',
                  'deadline': 'Крайний срок',
                  'worker_id': 'Выполняет',
                  'material_type': 'Тип материала',
                  'sched_id': 'Канал',
                  'task_status': 'Статус задачи'}

        widgets = {
            'ready_date': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date', 'id': "ready_date"}, format='%Y-%m-%d'),
            'sched_date': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date', 'id': "sched_date"}, format='%Y-%m-%d'),
            'deadline': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date', 'id': "deadline"}, format='%Y-%m-%d'),
            'worker_id': forms.Select(
                attrs={'class': "form-select", 'id': "worker_id"}, choices=choice.workers),
            'material_type': forms.Select(
                attrs={'class': "form-select", 'id': "material_type"}, choices=choice.material_type),
            'sched_id': forms.Select(
                attrs={'class': "form-select", 'id': "sched_id"}, choices=choice.schedules),
            'task_status': forms.Select(
                attrs={'class': "form-select", 'id': "task_status"}, choices=choice.task_status),
        }
class TaskSearchForm(forms.ModelForm):
    class Meta:
        model = TaskSearch
        fields = ('search_type', 'search_input', 'sql_set', 'order', 'order_type')

        labels = {'search_type': '', 'search_input': '', 'sql_set': 'Показать'}

        widgets = {
            'search_type': forms.Select(
                attrs={'class': 'form-select', 'id': 'search_type', 'style': 'max-width: 8rem;'},
                choices=((0, 'id'), (1, 'названию'))),
            'search_input': forms.TextInput(
                attrs={'class': 'form-control', 'id': 'search_input', 'placeholder': 'введите название передачи ...'},
            ),
            'sql_set': forms.Select(
                attrs={'class': 'form-select', 'id': 'sql_set', 'style': 'max-width: 11rem;'},
                choices=choice.sql_set()),
            'order': forms.TextInput(
                attrs={'class': 'visually-hidden', 'id': 'order'},
            ),
            'order_type': forms.TextInput(
                attrs={'class': 'visually-hidden', 'id': 'order_type'},
            ),
        }

class DynamicSelector(forms.Form):
    def __init__(self, program_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.program_id = program_id

        self.fields['workers_selector'] = forms.ChoiceField(
            widget=forms.Select(
            attrs={'class': 'form-select form-select-sm', 'id': f"workers_selector_{self.program_id}"}),
            label='Исполнитель',
            choices=choice.workers,
            required=False)
        self.fields['work_date_selector'] = forms.DateField(
            widget=forms.DateInput(
                attrs={'class': 'form-control form-control-sm', 'type': 'date', 'id': f"work_date_selector_{self.program_id}"},
                format='%Y-%m-%d'),
            label='Дата отсмотра',
            required=False)
        self.fields['status_selector'] = forms.ChoiceField(
            widget=forms.Select(
            attrs={'class': 'form-select form-select-sm', 'id': f"status_selector_{self.program_id}"}),
            label='Статус',
            choices=choice.task_status,
            required=False)
        self.fields['file_path'] = forms.CharField(
            widget=forms.TextInput(
                attrs={'class': 'form-control form-control-sm', 'id': f"file_path_{self.program_id}"}),
            label='Имя файла',
            required=False)