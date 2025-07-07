from django import forms
from .models import OtkModel
from main.form_choices import Choices


choice = Choices()

class OtkForm(forms.ModelForm):
    class Meta:
        model = OtkModel
        fields = ('ready_date', 'sched_date', 'deadline', 'engineer_id', 'material_type', 'sched_id', 'task_status')
        labels = {'ready_date': 'Дата отсмотра',
                  'sched_date': 'Дата эфира',
                  'deadline': 'Крайний срок',
                  'engineer_id': 'Выполняет',
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
            'engineer_id': forms.Select(
                attrs={'class': "form-select", 'id': "engineer_id"}, choices=choice.engineers),
            'material_type': forms.Select(
                attrs={'class': "form-select", 'id': "material_type"}, choices=choice.material_type),
            'sched_id': forms.Select(
                attrs={'class': "form-select", 'id': "sched_id"}, choices=choice.schedules),
            'task_status': forms.Select(
                attrs={'class': "form-select", 'id': "task_status"}, choices=choice.task_status),
        }

