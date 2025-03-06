from django import forms
from .models import ListFilter

class MyForm(forms.Form):
    choices = [('1', 'Канал+'), ('2', 'Советское'), ('3', 'Наше детство')]
    selected_choices = forms.MultipleChoiceField(choices=choices, widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
    )

class PostForm(forms.ModelForm):
    class Meta:
        channels = [(2, 'Крепкое кино'),
                    (3, 'Семейное кино'),
                    (4, 'Мировой сериал'),
                    (5, 'Наше родное кино'),
                    (6, 'Мужской сериал'),
                    (7, 'Романтичный сериал'),
                    (8, 'Планета дети'),
                    (9, 'Наше детство'),
                    (10, 'Советское родное кино'),
                    (12, 'Кино +')]
        workers = [(0, 'Александр Кисляков'),
                   (1, 'Ольга Кузовкина'),
                   (2, 'Дмитрий Гатенян'),
                   (3, 'Мария Сучкова'),
                   (4, 'Андрей Антипин'),
                   (5, 'Роман Рогачев'),
                   (6, 'Анастасия Чебакова'),
                   (7, 'Никита Кузаков'),
                   (8, 'Олег Кашежев'),
                   (9, 'Марфа Тарусина'),
                   (10, 'Евгений Доманов')]
        material_type = [(0, 'Фильм'), (1, 'Сериал')]
        status = [(0, 'Не готов'), (1, 'Готов'), (2, 'На доработке')]
        model = ListFilter
        fields = ('channels', 'workers', 'material_type', 'date', 'status')

        widgets = {
            'channels': forms.SelectMultiple(
                attrs={'class': 'ui selection dropdown gray', 'name': 'channels', 'id': 'channels'}, choices=channels),
            'workers': forms.SelectMultiple(
                attrs={'class': 'ui selection dropdown', 'name': 'workers', 'id': 'workers'}, choices=workers),
            'material_type': forms.Select(
                attrs={'class': 'ui selection dropdown', 'name': 'material_type', 'id': 'material_type'}, choices=material_type),
            'date': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(
                attrs={'class': 'ui selection dropdown', 'name': 'status', 'id': 'status'}, choices=status),
        }
