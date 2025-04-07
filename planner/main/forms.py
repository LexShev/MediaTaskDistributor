from django import forms

from .db_connection import program_custom_fields
from .models import ModelFilter


engineers_list = program_custom_fields().get(15)
engineers = [('', '-')]
if engineers_list:
    for engineer in enumerate(engineers_list.split('\r\n')):
        if engineer[1]:
            engineers.append(engineer)

tags_list = program_custom_fields().get(18)
tags = [('', '-')]
if tags_list:
    for tag in enumerate(tags_list.split('\r\n')):
        if tag[1]:
            tags.append(tag)

inoagents_list = program_custom_fields().get(19)
inoagents = [('', '-')]
if inoagents_list:
    for inoagent in enumerate(inoagents_list.split('\r\n')):
        if inoagent[1]:
            inoagents.append(inoagent)

rate = (('', '-'), (0, '0+'), (1, '6+'), (2, '12+'), (3, '16+'), (4, '18+'))

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

class MyForm(forms.Form):
    choices = [('1', 'Канал+'), ('2', 'Советское'), ('3', 'Наше детство')]
    selected_choices = forms.MultipleChoiceField(choices=choices, widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
    )

class ListForm(forms.ModelForm):
    class Meta:


        material_type = [('', 'Тип материала'),
                         ('film', 'Фильм'),
                         ('season', 'Сериал')]
        task_status = [('', 'Статус'),
                       ('not_ready', 'Не готов'),
                       ('ready', 'Готов'),
                       ('fix', 'На доработке')]
        model = ModelFilter
        fields = ('channels', 'engineers', 'material_type', 'work_dates', 'task_status')

        widgets = {
            'channels': forms.SelectMultiple(
                attrs={'class': 'ui selection dropdown', 'id': 'channels'}, choices=channels),
            'engineers': forms.SelectMultiple(
                attrs={'class': 'ui selection dropdown', 'id': 'engineers'}, choices=engineers),
            'material_type': forms.SelectMultiple(
                attrs={'class': 'ui selection dropdown', 'id': 'material_type'}, choices=material_type),
            'work_dates': forms.DateInput(
                attrs={'class': 'form-control', 'data-bs-theme': 'light', 'type': 'text'}),
                # , 'data-bs-theme': "light"
            'task_status': forms.SelectMultiple(
                attrs={'class': 'ui selection dropdown', 'id': 'task_status', 'placeholder': 'test'}, choices=task_status),
        }

class WeekForm(forms.ModelForm):
    class Meta:
        material_type = [('', 'Тип материала'),
                         ('film', 'Фильм'),
                         ('season', 'Сериал')]
        task_status = [('', 'Статус'),
                       ('not_ready', 'Не готов'),
                       ('ready', 'Готов'),
                       ('fix', 'На доработке')]
        model = ModelFilter
        fields = ('channels', 'engineers', 'material_type', 'task_status')
        widgets = {
            'channels': forms.SelectMultiple(
                attrs={'class': 'ui selection dropdown', 'id': 'channels'}, choices=channels),
            'engineers': forms.SelectMultiple(
                attrs={'class': 'ui selection dropdown', 'id': 'engineers'}, choices=engineers),
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
    # engineers = [(0, '-'), (0, 'Александр Кисляков'), (1, 'Ольга Кузовкина'), (2, 'Дмитрий Гатенян'), (3, 'Мария Сучкова'), (4, 'Андрей Антипин'), (
    # 5, 'Роман Рогачев'), (6, 'Анастасия Чебакова'), (7, 'Никита Кузаков'), (8, 'Олег Кашежев'), (9, 'Марфа Тарусина'), (10, 'Евгений Доманов')]
    meta_form = forms.ChoiceField(widget=forms.Select(
        attrs={'class': 'form-select', 'id': "meta_form"}),
        label='Meta', choices=((0, 'Нет'), (1, 'Да')), required=False)
    work_date_form = forms.DateField(widget=forms.DateInput(
        attrs={'class': 'form-control', 'type': 'date', 'id': "work_date_form"}),
        label='Дата отсмотра', required=False)
    cenz_rate_form = forms.ChoiceField(widget=forms.Select(
        attrs={'class': "form-select", 'id': "cenz_rate_form"}),
        label='Ценз отсмотра', choices=rate)
    engineers_form = forms.ChoiceField(widget=forms.Select(
        attrs={'class': "form-select", 'id': "engineers_form"}),
        label='Тайтл проверил', choices=engineers, required=False)
    # tags_form = forms.ChoiceField(widget=forms.Select(
    #     attrs={'class': "form-select", 'id': "tags_form"}),
    #     label='Теги', choices=tags, required=False)
    inoagent_form = forms.ChoiceField(
        widget=forms.Select(attrs={'class': "form-select", 'id': "inoagent_form"}),
        label='Иноагент', choices=inoagents, required=False)


class KpiForm(forms.Form):

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
    engineers_form = forms.ChoiceField(widget=forms.Select(
        attrs={'class': "form-select", 'id': "engineers_form"}),
        label='Выполняет', choices=engineers, required=False)
    material_type_form = forms.ChoiceField(widget=forms.Select(
        attrs={'class': "form-select", 'id': "material_type_form"}),
        label='Тип материала', choices=material_type, required=False)
    task_status_form = forms.ChoiceField(widget=forms.Select(
        attrs={'class': "form-select", 'id': "task_status_form"}),
        label='Статус задачи', choices=task_status, required=False)

class VacationForm(forms.Form):
    engineers_form = forms.ChoiceField(widget=forms.Select(
        attrs={'class': "form-select", 'id': "engineers_form"}),
        label='Сотрудник', choices=engineers, required=True)
    start_date_form = forms.DateField(widget=forms.DateInput(
        attrs={'class': 'form-control', 'type': 'date', 'id': "start_date_form"}),
        label='Начало отпуска', required=True)
    end_date_form = forms.DateField(widget=forms.DateInput(
        attrs={'class': 'form-control', 'type': 'date', 'id': "end_date_form"}),
        label='Конец отпуска', required=True)
    description_form = forms.CharField(widget=forms.Textarea(
        attrs={'class': "form-control", 'id': "description_form", 'style': "height: 60px"}),
        label='Примечание', required=False)

