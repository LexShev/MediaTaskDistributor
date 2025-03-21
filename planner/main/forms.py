from django import forms

from .db_connection import program_custom_fields
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
                         ('film', 'Фильм'),
                         ('season', 'Сериал')]
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
                # , 'data-bs-theme': "light"
            'task_status': forms.SelectMultiple(
                attrs={'class': 'ui selection dropdown', 'id': 'task_status', 'placeholder': 'test'}, choices=task_status),
        }

class WeekForm(forms.ModelForm):
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
                         ('film', 'Фильм'),
                         ('season', 'Сериал')]
        task_status = [('', 'Статус'),
                       ('not_ready', 'Не готов'),
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

class CenzFormText(forms.Form):
    lgbt_form = forms.CharField(widget=forms.Textarea(
        attrs={'class': "form-control", 'id': "lgbt_form", 'style': "height: 130px"}),
        label='ЛГБТ', required=False)
    sig_form = forms.CharField(widget=forms.Textarea(
        attrs={'class': "form-control", 'id': "sig_form", 'style': "height: 130px"}),
        label='Сигареты', required=False)
    obnazh_form = forms.CharField(widget=forms.Textarea(
        attrs={'class': "form-control", 'id': "obnazh_form", 'style': "height: 130px"}),
        label='Обнаженка', required=False)
    narc_form = forms.CharField(widget=forms.Textarea(
        attrs={'class': "form-control", 'id': "narc_form", 'style': "height: 130px"}),
        label='Наркотики', required=False)
    mat_form = forms.CharField(widget=forms.Textarea(
        attrs={'class': "form-control", 'id': "mat_form", 'style': "height: 130px"}),
        label='Мат', required=False)
    other_form = forms.CharField(widget=forms.Textarea(
        attrs={'class': "form-control", 'id': "other_form", 'style': "height: 130px"}),
        label='Другое', required=False)
    editor_form = forms.CharField(widget=forms.Textarea(
        attrs={'class': "form-control", 'id': "editor_form", 'style': "height: 130px"}),
        label='Редакторские замечания', required=False)

class CenzFormDropDown(forms.Form):
    workers = [('', '-'),
               ('Александр Кисляков', 'Александр Кисляков'),
               ('Ольга Кузовкина', 'Ольга Кузовкина'),
               ('Дмитрий Гатенян', 'Дмитрий Гатенян'),
               ('Мария Сучкова', 'Мария Сучкова'),
               ('Андрей Антипин', 'Андрей Антипин'),
               ('Роман Рогачев', 'Роман Рогачев'),
               ('Анастасия Чебакова', 'Анастасия Чебакова'),
               ('Никита Кузаков', 'Никита Кузаков'),
               ('Олег Кашежев', 'Олег Кашежев'),
               ('Марфа Тарусина', 'Марфа Тарусина'),
               ('Евгений Доманов', 'Евгений Доманов')]

    workers_list = program_custom_fields().get(15)
    workers = [(0, '-')]
    if workers_list:
        for worker in enumerate(workers_list.split('\r\n')):
            if worker[1]:
                workers.append(worker)

    tags_list = program_custom_fields().get(18)
    tags = [(0, '-')]
    if tags_list:
        for tag in enumerate(tags_list.split('\r\n')):
            if tag[1]:
                tags.append(tag)

    inoagents_list = program_custom_fields().get(19)
    inoagents = [(0, '-')]
    if inoagents_list:
        for inoagent in enumerate(inoagents_list.split('\r\n')):
            if inoagent[1]:
                inoagents.append(inoagent)

    rate = (('0+', '0+'), ('6+', '6+'), ('12+', '12+'), ('16+', '16+'), ('18+', '18+'))
    meta_form = forms.ChoiceField(widget=forms.Select(
        attrs={'class': 'form-select', 'id': "meta_form"}),
        label='Meta', choices=((0, 'Нет'), (1, 'Да')), required=False)
    work_date_form = forms.DateField(widget=forms.DateInput(
        attrs={'class': 'form-control', 'type': 'date', 'id': "work_date_form"}),
        label='Дата отсмотра', required=False)
    cenz_rate_form = forms.ChoiceField(widget=forms.Select(
        attrs={'class': "form-select", 'id': "cenz_rate_form"}),
        label='Ценз отсмотра', choices=rate)
    cenz_worker_form = forms.ChoiceField(widget=forms.Select(
        attrs={'class': "form-select", 'id': "cenz_worker_form"}),
        label='Тайтл проверил', choices=workers, required=False)
    tags_form = forms.ChoiceField(widget=forms.Select(
        attrs={'class': "form-select", 'id': "tags_form"}),
        label='Теги', choices=tags, required=False)
    inoagent_form = forms.ChoiceField(
        widget=forms.Select(attrs={'class': "form-select", 'id': "inoagent_form"}),
        label='Иноагент', choices=inoagents, required=False)


class KpiForm(forms.Form):
    workers = [('', '-'),
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
    task_status = [('', '-'),
                   ('not_ready', 'Не готов'),
                   ('ready', 'Готов'),
                   ('fix', 'На доработке')]

    material_type = [('', '-'),
                     ('film', 'Фильм'),
                     ('season', 'Сериал')]

    work_date_form = forms.DateField(widget=forms.DateInput(
        attrs={'class': 'form-control', 'type': 'date', 'id': "work_date_form"}),
        label='Дата отсмотра', required=False)
    workers_form = forms.ChoiceField(widget=forms.Select(
        attrs={'class': "form-select", 'id': "cenz_worker_form"}),
        label='Выполняет', choices=workers, required=False)
    material_type_form = forms.ChoiceField(widget=forms.Select(
        attrs={'class': "form-select", 'id': "material_type_form"}),
        label='Тип материала', choices=material_type, required=False)
    task_status_form = forms.ChoiceField(widget=forms.Select(
        attrs={'class': "form-select", 'id': "task_status_form"}),
        label='Статус задачи', choices=task_status, required=False)
