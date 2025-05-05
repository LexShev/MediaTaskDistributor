from django import forms

from .models import AdvancedSearch


class AdvancedSearchForm(forms.ModelForm):
    class Meta:
        model = AdvancedSearch
        fields = ('search_id',)
        choices = (
            (0, 'id'),
            (1, 'названию'),
            (2, 'имени файла'),
            (3, 'исполнителю'),
            (4, 'дате эфира'),
            (5, 'крайнему сроку'),
        )
        labels = {'search_id': 'поиск по'}

        widgets = {
            'search_id': forms.Select(
                attrs={'class': 'form-select', 'id': 'search_id'},
                choices=choices
            ),
        }