from django import forms
from django.core.exceptions import ValidationError

from .models import ModelFilter, AttachedFiles, ModelSorting
from .form_choices import choice


def validate_file_type(value):
    valid_types = [
        'image/jpeg', 'image/png', 'image/gif',
        'video/mp4', 'video/quicktime',
        'audio/mpeg', 'audio/wav', 'audio/aac', 'audio/x-aac', 'audio/vnd.dlna.adts',
        'text/plain',
        'application/pdf',
        'application/octet-stream',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ]

    if value.content_type not in valid_types:
        print('Запрещённый формат', value.content_type)
        raise ValidationError('Недопустимый тип файла')

class ListFilter(forms.ModelForm):
    class Meta:
        model = ModelFilter
        fields = ('schedules', 'workers', 'material_type', 'work_dates', 'task_status')
        labels = {
            'schedules': 'Каналы', 'workers': 'Исполнители',
            'material_type': 'Тип материала', 'work_dates': 'Назначенная дата исполнения',
            'task_status': 'Статус материала',
        }
        widgets = {
            'schedules': forms.SelectMultiple(
                attrs={'class': 'ui selection dropdown', 'id': 'schedules'},
                choices=choice.schedules('Канал')),
            'workers': forms.SelectMultiple(
                attrs={'class': 'ui selection dropdown', 'id': 'workers'},
                choices=choice.workers('Выполняет')),
            'material_type': forms.SelectMultiple(
                attrs={'class': 'ui selection dropdown', 'id': 'material_type'},
                choices=choice.material_type('Тип материала')),
            'work_dates': forms.DateInput(
                attrs={'class': 'form-control', 'data-bs-theme': 'light', 'type': 'text'}),
            'task_status': forms.SelectMultiple(
                attrs={'class': 'ui selection dropdown', 'id': 'task_status'},
                choices=choice.task_status('Статус')),
        }

class WeekFilter(forms.ModelForm):
    class Meta:
        model = ModelFilter
        fields = ('schedules', 'workers', 'material_type', 'task_status')
        labels = {
            'schedules': 'Каналы', 'workers': 'Исполнители',
            'material_type': 'Тип материала', 'task_status': 'Статус материала',
        }
        widgets = {
            'schedules': forms.SelectMultiple(
                attrs={'class': 'ui selection dropdown', 'id': 'schedules'},
                choices=choice.schedules('Канал')),
            'workers': forms.SelectMultiple(
                attrs={'class': 'ui selection dropdown', 'id': 'workers'},
                choices=choice.workers('Выполняет')),
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

    def __init__(self, *args, **kwargs):
        comparison_data = kwargs.pop('comparison_data', {})
        super(CenzFormText, self).__init__(*args, **kwargs)

        if comparison_data:
            for field_name, field_value in comparison_data.items():
                if not self.fields.get(field_name):
                    continue
                self.fields[field_name].initial = field_value

                if field_value == 'несколько значений':
                    label = self.fields[field_name].label
                    self.fields[field_name].label = f'{label}\n<{field_value}>'
                    self.fields[field_name].initial = ''


class CenzFormDropDown(forms.Form):
    work_date_form = forms.DateField(widget=forms.DateInput(
        attrs={'class': 'form-control', 'type': 'date', 'id': "work_date_form"}, format='%Y-%m-%d'),
        label='Дата отсмотра', required=False)
    cenz_rate_form = forms.ChoiceField(widget=forms.Select(
        attrs={'class': "form-select", 'id': "cenz_rate_form"}),
        label='Ценз отсмотра', choices=choice.rate(), required=False)
    engineers_form = forms.ChoiceField(widget=forms.Select(
        attrs={'class': "form-select", 'id': "engineers_form"}),
        label='Тайтл проверил', choices=choice.engineers(), required=False)
    # tags_form = forms.ChoiceField(widget=forms.Select(
    #     attrs={'class': "form-select", 'id': "tags_form"}),
    #     label='Теги', choices=choice.tags(), required=False)
    inoagent_form = forms.ChoiceField(
        widget=forms.Select(attrs={'class': "form-select", 'id': "inoagent_form"}),
        label='Иноагент', choices=choice.inoagents, required=False)
    narc_select_form = forms.ChoiceField(widget=forms.Select(
        attrs={'class': 'form-select', 'id': "narc_select_form"}),
        label='Наркотики', choices=((0, 'Нет'), (1, 'Да')), required=False)
    meta_form = forms.ChoiceField(widget=forms.Select(
        attrs={'class': 'form-select', 'id': "meta_form"}),
        label='Meta', choices=((0, 'Нет'), (1, 'Да')), required=False)

    def __init__(self, *args, **kwargs):
        comparison_data = kwargs.pop('comparison_data', {})
        super(CenzFormDropDown, self).__init__(*args, **kwargs)

        if comparison_data:
            for field_name, field_value in comparison_data.items():
                if not self.fields.get(field_name):
                    continue
                self.fields[field_name].initial = field_value

                if field_value == 'несколько значений':
                    label = self.fields[field_name].label
                    self.fields[field_name].label = f'{label} <{field_value}>'
                    self.fields[field_name].initial = ''


class KpiForm(forms.Form):
    work_date_form = forms.DateField(widget=forms.DateInput(
        attrs={'class': 'form-control', 'type': 'date', 'id': "work_date_form"}),
        label='Назначенная дата', required=False)
    workers_form = forms.ChoiceField(widget=forms.Select(
        attrs={'class': "form-select", 'id': "workers_form"}),
        label='Выполняет', choices=choice.workers(), required=False)
    material_type_form = forms.ChoiceField(widget=forms.Select(
        attrs={'class': "form-select", 'id': "material_type_form"}),
        label='Тип материала', choices=choice.material_type(), required=False)
    task_status_form = forms.ChoiceField(widget=forms.Select(
        attrs={'class': "form-select", 'id': "task_status_form"}),
        label='Статус задачи', choices=choice.task_status(), required=False)


class VacationForm(forms.Form):
    workers_form = forms.ChoiceField(widget=forms.Select(
        attrs={'class': "form-select", 'id': "workers_form"}),
        label='Сотрудник', choices=choice.workers(), required=True)
    start_date_form = forms.DateField(widget=forms.DateInput(
        attrs={'class': 'form-control', 'type': 'date', 'id': "start_date_form"}),
        label='Начало отпуска', required=True)
    end_date_form = forms.DateField(widget=forms.DateInput(
        attrs={'class': 'form-control', 'type': 'date', 'id': "end_date_form"}),
        label='Конец отпуска', required=True)
    description_form = forms.CharField(widget=forms.Textarea(
        attrs={'class': "form-control", 'id': "description_form", 'style': "height: 60px"}),
        label='Примечание', required=False)


class AttachedFilesForm(forms.ModelForm):
    file_path = forms.FileField(
        required=True,
        validators=[validate_file_type],
        label='Прикрепить файл',
        widget=forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*, video/*, audio/*, .pdf, .doc, .docx, .srt'
            })
        )
    class Meta:
        model = AttachedFiles
        fields = ('description', 'file_path')
        labels = {'description': 'Описание',}
        widgets = {
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'style': 'min-width: 51%;',
                'placeholder': 'Добавьте описание...'
            }),
        }

class SortingForm(forms.ModelForm):
    class Meta:
        model = ModelSorting
        fields = ('user_order', 'order_type')
        widgets = {
            'user_order': forms.Select(
                attrs={'class': 'form-select text-end', 'id': 'user_order'},
                choices=choice.sorting()
            ),
            'order_type': forms.Select(
                attrs={'class': 'form-select text-end mb-3', 'id': 'order_type'},
                choices=(('ASC', 'возрастанию'), ('DESC', 'убыванию'))
            ),
        }
