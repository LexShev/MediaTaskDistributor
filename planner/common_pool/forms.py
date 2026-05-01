from django import forms

from main.form_choices import get_choice
from .models import CommonPool


class CommonPoolForm(forms.ModelForm):
    class Meta:
        model = CommonPool
        fields = ('search_type', 'material_type', 'search_input', 'sql_set')

        labels = {'search_type': '', 'material_type': '', 'search_input': 'Строка поиска', 'sql_set': 'Показать'}

        widgets = {
            'search_type': forms.Select(
                attrs={'class': 'form-select', 'id': 'search_type', 'style': 'width: 5rem;'},
                choices=((0, 'id'), (1, 'названию'))),
            'material_type': forms.Select(
                attrs={'class': 'form-select', 'id': 'material_type', 'style': 'width: 5rem;'},
                choices=((0, 'всему'), (1, 'фильмам'), (2, 'сериалам'))),
            'search_input': forms.TextInput(
                attrs={'class': 'form-control', 'id': 'search_input', 'placeholder': 'введите название передачи ...',
                       'style': 'width: 54rem;'},
                ),
            'sql_set': forms.Select(
                attrs={'class': 'form-select', 'id': 'sql_set', 'style': 'width: 8rem;'},
                choices=get_choice().sql_set()),
        }
