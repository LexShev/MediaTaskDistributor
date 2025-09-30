from django import forms

from main.form_choices import choice
from .models import AdvancedSearch


class AdvancedSearchForm(forms.ModelForm):
    class Meta:
        model = AdvancedSearch
        fields = ('search_id', 'engineers', 'sql_set')
        choices = (
            (0, 'id'),
            (1, 'названию'),
            (2, 'имени файла'),
            (3, 'исполнителю'),
            (4, 'дате эфира'),
            (5, 'крайнему сроку'),
        )
        labels = {'search_id': 'поиск по', 'engineers': 'Укажите сотрудника', 'sql_set': 'Показать'}

        widgets = {
            'search_id': forms.Select(
                attrs={'class': 'form-select', 'id': 'search_id', 'style': 'width: 6rem;'},
                choices=choices
            ),
            'engineers': forms.Select(
                attrs={'class': 'form-select', 'id': 'engineers', 'style': 'width: 80rem;'},
                choices=choice.engineers()),
            'sql_set': forms.Select(
                attrs={'class': 'form-select', 'id': 'sql_set', 'style': 'width: 6rem;'},
                choices=choice.sql_set()),
        }

