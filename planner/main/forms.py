from django import forms

# from .db_connection import program_custom_fields
from .models import ModelFilter, AdvancedSearch
from .form_choices import Choices


# engineers_list = program_custom_fields().get(15)
# engineers = [('', '-')]
# if engineers_list:
#     for engineer in enumerate(engineers_list.split('\r\n')):
#         if engineer[1]:
#             engineers.append(engineer)
#
# tags_list = program_custom_fields().get(18)
# tags = [('', '-')]
# if tags_list:
#     for tag in enumerate(tags_list.split('\r\n')):
#         if tag[1]:
#             tags.append(tag)
#
# inoagents_list = program_custom_fields().get(19)
# inoagents = [('', '-')]
# if inoagents_list:
#     for inoagent in enumerate(inoagents_list.split('\r\n')):
#         if inoagent[1]:
#             inoagents.append(inoagent)
#
# rate = (('', '-'), (0, '0+'), (1, '6+'), (2, '12+'), (3, '16+'), (4, '18+'))
#
# schedules = [
#     (3, 'Крепкое'),
#     (5, 'Планета дети'),
#     (6, 'Мировой сериал'),
#     (7, 'Мужской сериал'),
#     (8, 'Наше детство'),
#     (9, 'Романтичный сериал'),
#     (10, 'Наше родное кино'),
#     (11, 'Семейное кино'),
#     (12, 'Советское родное кино'),
#     (20, 'Кино +')
# ]

choice = Choices()

class ListFilter(forms.ModelForm):
    class Meta:
        model = ModelFilter
        fields = ('schedules', 'engineers', 'material_type', 'work_dates', 'task_status')

        widgets = {
            'schedules': forms.SelectMultiple(
                attrs={'class': 'ui selection dropdown', 'id': 'schedules'},
                choices=choice.schedules('Канал')),
            'engineers': forms.SelectMultiple(
                attrs={'class': 'ui selection dropdown', 'id': 'engineers'},
                choices=choice.engineers('Выполняет')),
            'material_type': forms.SelectMultiple(
                attrs={'class': 'ui selection dropdown', 'id': 'material_type'},
                choices=choice.material_type('Тип материала')),
            'work_dates': forms.DateInput(
                attrs={'class': 'form-control', 'data-bs-theme': 'light', 'type': 'text'}),
                # , 'data-bs-theme': "light"
            'task_status': forms.SelectMultiple(
                attrs={'class': 'ui selection dropdown', 'id': 'task_status', 'placeholder': 'test'},
                choices=choice.task_status('Статус')),
        }

class WeekFilter(forms.ModelForm):
    class Meta:
        model = ModelFilter
        fields = ('schedules', 'engineers', 'material_type', 'task_status')
        widgets = {
            'schedules': forms.SelectMultiple(
                attrs={'class': 'ui selection dropdown', 'id': 'schedules'},
                choices=choice.schedules('Канал')),
            'engineers': forms.SelectMultiple(
                attrs={'class': 'ui selection dropdown', 'id': 'engineers'},
                choices=choice.engineers('Выполняет')),
            'material_type': forms.SelectMultiple(
                attrs={'class': 'ui selection dropdown', 'id': 'material_type'},
                choices=choice.material_type('Тип материала')),
            'task_status': forms.SelectMultiple(
                attrs={'class': 'ui selection dropdown', 'id': 'task_status'},
                choices=choice.task_status('Статус')),
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
    narc_form = forms.ChoiceField(widget=forms.Select(
        attrs={'class': 'form-select', 'id': "narc_form"}),
        label='Наркотики', choices=((0, 'Нет'), (1, 'Да')), required=False)
    meta_form = forms.ChoiceField(widget=forms.Select(
        attrs={'class': 'form-select', 'id': "meta_form"}),
        label='Meta', choices=((0, 'Нет'), (1, 'Да')), required=False)
    work_date_form = forms.DateField(widget=forms.DateInput(
        attrs={'class': 'form-control', 'type': 'date', 'id': "work_date_form"}),
        label='Дата отсмотра', required=False)
    cenz_rate_form = forms.ChoiceField(widget=forms.Select(
        attrs={'class': "form-select", 'id': "cenz_rate_form"}),
        label='Ценз отсмотра', choices=choice.rate())
    engineers_form = forms.ChoiceField(widget=forms.Select(
        attrs={'class': "form-select", 'id': "engineers_form"}),
        label='Тайтл проверил', choices=choice.engineers, required=False)
    # tags_form = forms.ChoiceField(widget=forms.Select(
    #     attrs={'class': "form-select", 'id': "tags_form"}),
    #     label='Теги', choices=choice.tags(), required=False)
    inoagent_form = forms.ChoiceField(
        widget=forms.Select(attrs={'class': "form-select", 'id': "inoagent_form"}),
        label='Иноагент', choices=choice.inoagents, required=False)


class KpiForm(forms.Form):

    work_date_form = forms.DateField(widget=forms.DateInput(
        attrs={'class': 'form-control', 'type': 'date', 'id': "work_date_form"}),
        label='Дата отсмотра', required=False)
    engineers_form = forms.ChoiceField(widget=forms.Select(
        attrs={'class': "form-select", 'id': "engineers_form"}),
        label='Выполняет', choices=choice.engineers, required=False)
    material_type_form = forms.ChoiceField(widget=forms.Select(
        attrs={'class': "form-select", 'id': "material_type_form"}),
        label='Тип материала', choices=choice.material_type(), required=False)
    task_status_form = forms.ChoiceField(widget=forms.Select(
        attrs={'class': "form-select", 'id': "task_status_form"}),
        label='Статус задачи', choices=choice.task_status(), required=False)

class VacationForm(forms.Form):
    engineers_form = forms.ChoiceField(widget=forms.Select(
        attrs={'class': "form-select", 'id': "engineers_form"}),
        label='Сотрудник', choices=choice.engineers, required=True)
    start_date_form = forms.DateField(widget=forms.DateInput(
        attrs={'class': 'form-control', 'type': 'date', 'id': "start_date_form"}),
        label='Начало отпуска', required=True)
    end_date_form = forms.DateField(widget=forms.DateInput(
        attrs={'class': 'form-control', 'type': 'date', 'id': "end_date_form"}),
        label='Конец отпуска', required=True)
    description_form = forms.CharField(widget=forms.Textarea(
        attrs={'class': "form-control", 'id': "description_form", 'style': "height: 60px"}),
        label='Примечание', required=False)

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