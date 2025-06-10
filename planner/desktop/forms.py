from django import forms

from desktop.models import ModelDeskTopFilter
from main.form_choices import Choices


choice = Choices()

class DeskTopFilter(forms.ModelForm):
    class Meta:
        model = ModelDeskTopFilter
        fields = ('schedules', 'material_type', 'work_dates', 'task_status')

        widgets = {
            'schedules': forms.SelectMultiple(
                attrs={'class': 'ui selection dropdown', 'id': 'schedules'},
                choices=choice.schedules('Канал')),
            'material_type': forms.SelectMultiple(
                attrs={'class': 'ui selection dropdown', 'id': 'material_type'},
                choices=choice.material_type('Тип материала')),
            'work_dates': forms.DateInput(
                attrs={'class': 'form-control', 'data-bs-theme': 'light', 'type': 'text'}),
            'task_status': forms.SelectMultiple(
                attrs={'class': 'ui selection dropdown', 'id': 'task_status', 'placeholder': 'test'},
                choices=choice.task_status('Статус')),
        }