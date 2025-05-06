from django import forms

from main.form_choices import Choices
from .models import CommonPool

choice = Choices()
class CommonPoolForm(forms.ModelForm):
    class Meta:
        model = CommonPool
        fields = ('sql_set',)

        labels = {'sql_set': 'Показать'}

        widgets = {
            'sql_set': forms.Select(
                attrs={'class': 'form-select', 'id': 'sql_set', 'style': 'width: 8rem;'},
                choices=choice.sql_set()),
        }

