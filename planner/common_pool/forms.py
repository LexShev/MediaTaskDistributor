from django import forms

from main.form_choices import choice
from .models import CommonPool


class CommonPoolForm(forms.ModelForm):
    class Meta:
        model = CommonPool
        fields = ('search_type', 'search_input', 'sql_set')

        labels = {'search_type': '', 'search_input': 'Строка поиска', 'sql_set': 'Показать'}

        widgets = {
            'search_type': forms.Select(
                attrs={'class': 'form-select', 'id': 'search_type', 'style': 'width: 4rem;'},
                choices=((0, 'id'), (1, 'названию'))),
            'search_input': forms.TextInput(
                attrs={'class': 'form-control', 'id': 'search_input', 'placeholder': 'введите название передачи ...',
                       'style': 'width: 60rem;'},
                ),
            'sql_set': forms.Select(
                attrs={'class': 'form-select', 'id': 'sql_set', 'style': 'width: 8rem;'},
                choices=choice.sql_set()),
        }
