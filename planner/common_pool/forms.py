from django import forms

from main.form_choices import Choices
from .models import CommonPool

choice = Choices()
class CommonPoolForm(forms.ModelForm):
    class Meta:
        model = CommonPool
        fields = ('search_type', 'sql_set')

        labels = {'search_type': '', 'sql_set': 'Показать'}

        widgets = {
            'search_type': forms.Select(
                attrs={'class': 'form-select', 'id': 'search_type', 'style': 'width: 4rem;'},
                choices=((0, 'id'), (1, 'названию'))),
            'sql_set': forms.Select(
                attrs={'class': 'form-select', 'id': 'sql_set', 'style': 'width: 8rem;'},
                choices=choice.sql_set()),
        }

