from distribution.models import Distribution
from django import forms

from main.form_choices import choice


class DistributionForm(forms.ModelForm):
    class Meta:
        model = Distribution
        fields = ('distr_sched_end_date', 'distr_sched_id')

        labels = {'distr_sched_end_date': 'Дата завершения распределения', 'distr_sched_id': 'Каналы'}

        widgets = {
            'distr_sched_end_date': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date', 'id': "distr_sched_end_date"}, format='%Y-%m-%d'),
            'distr_sched_id': forms.Select(
                attrs={'class': "form-select", 'id': "distr_sched_id"}, choices=choice.schedules(label='Все')),
        }