from django import forms
from .models import MainFilter

class MyForm(forms.Form):
    choices = [('1', 'Канал+'), ('2', 'Советское'), ('3', 'Наше детство')]
    selected_choices = forms.MultipleChoiceField(choices=choices, widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
    )

class ListForm(forms.ModelForm):
    class Meta:
        channels = [('', 'Телеканал'),
                    (2, 'Крепкое кино'),
                    (3, 'Семейное кино'),
                    (4, 'Мировой сериал'),
                    (5, 'Наше родное кино'),
                    (6, 'Мужской сериал'),
                    (7, 'Романтичный сериал'),
                    (8, 'Планета дети'),
                    (9, 'Наше детство'),
                    (10, 'Советское родное кино'),
                    (12, 'Кино +')]
        workers = [('', 'Выполняет'),
                   (0, 'Александр Кисляков'),
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
        material_type = [('', 'Тип материала'),
                         ((5, 6, 10, 11), 'Фильм'),
                         ((4, 12), 'Сериал')]
        task_status = [('', 'Статус'),
                       ('not_ready', 'Не готов'),
                       ('ready', 'Готов'),
                       ('fix', 'На доработке')]
        model = MainFilter
        fields = ('channels', 'workers', 'material_type', 'work_dates', 'task_status')

        widgets = {
            'channels': forms.SelectMultiple(
                attrs={'class': 'ui selection dropdown', 'id': 'channels'}, choices=channels),
            'workers': forms.SelectMultiple(
                attrs={'class': 'ui selection dropdown', 'id': 'workers'}, choices=workers),
            'material_type': forms.SelectMultiple(
                attrs={'class': 'ui selection dropdown', 'id': 'material_type'}, choices=material_type),
            'work_dates': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'}),
            'task_status': forms.SelectMultiple(
                attrs={'class': 'ui selection dropdown', 'id': 'task_status', 'placeholder': 'test'}, choices=task_status),
        }

class WeekForm(forms.ModelForm):
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
        material_type = [((5, 6, 10, 11), 'Фильм'),
                         ((4, 12), 'Сериал')]
        task_status = [('not_ready', 'Не готов'),
                       ('ready', 'Готов'),
                       ('fix', 'На доработке')]
        model = MainFilter
        fields = ('channels', 'workers', 'material_type', 'task_status')

        widgets = {
            'channels': forms.SelectMultiple(
                attrs={'class': 'ui selection dropdown', 'id': 'channels'}, choices=channels),
            'workers': forms.SelectMultiple(
                attrs={'class': 'ui selection dropdown', 'id': 'workers'}, choices=workers),
            'material_type': forms.SelectMultiple(
                attrs={'class': 'ui selection dropdown', 'id': 'material_type'}, choices=material_type),
            'task_status': forms.SelectMultiple(
                attrs={'class': 'ui selection dropdown', 'id': 'task_status'}, choices=task_status),
        }