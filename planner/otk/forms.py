from django import forms
from .models import OtkModel, FormChoices




class OtkForm(forms.ModelForm):
    class Meta:
        model = OtkModel
        fields = ('ready_date', 'sched_date', 'engineer_id', 'material_type', 'sched_id', 'task_status')
        labels = {'ready_date': 'Дата отсмотра',
                  'sched_date': 'Дата эфира',
                  'engineer_id': 'Выполняет',
                  'material_type': 'Тип материала',
                  'sched_id': 'Канал',
                  'task_status': 'Статус задачи'}

        task_status = [('', '-'),
                       ('not_ready', 'Не готов'),
                       ('ready', 'Отсмотрен'),
                       ('fix', 'На доработке')]

        material_type = [('', '-'),
                         ('film', 'Фильм'),
                         ('season', 'Сериал')]

        widgets = {
            'ready_date': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date', 'id': "ready_date"}, format='%Y-%m-%d'),
            'sched_date': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date', 'id': "sched_date"}, format='%Y-%m-%d'),
            'engineer_id': forms.Select(
                attrs={'class': "form-select", 'id': "engineer_id"}, choices=FormChoices.Engineers.choices),
            'material_type': forms.Select(
                attrs={'class': "form-select", 'id': "material_type"}, choices=material_type),
            'sched_id': forms.Select(
                attrs={'class': "form-select", 'id': "sched_id"}, choices=FormChoices.SchedulesID.choices),
            'task_status': forms.Select(
                attrs={'class': "form-select", 'id': "task_status"}, choices=task_status),
        }

