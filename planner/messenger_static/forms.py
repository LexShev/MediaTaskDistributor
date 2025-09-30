from django import forms
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe

from .models import Message
from main.form_choices import choice


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


class DropdownMenuWidget(forms.Widget):
    def __init__(self, choices=None, attrs=None):
        super().__init__(attrs)
        self.choices = choices or []

    def render(self, name, value, attrs=None, renderer=None):
        html = ['<ul class="dropdown-menu" aria-labelledby="dropdownMenuButton">']
        for choice_value, choice_label in self.choices:
            html.append(
                f'<li class="dropdown-item" onclick="modifyMessage(this)" data-planner-worker-id="{choice_value}">{choice_label}</li>'
            )

        html.append('</ul>')
        return mark_safe('\n'.join(html))

class MessageForm(forms.ModelForm):
    file_path = forms.FileField(
        required=False,
        validators=[validate_file_type],
        widget=forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*, video/*, audio/*, .pdf, .doc, .docx, .srt'
            })
        )
    engineers_mention = forms.ChoiceField(
        required=False,
        widget=DropdownMenuWidget(attrs={}),
        choices=choice.planner_workers(exclude_init=True)
    )

    class Meta:
        model = Message
        fields = ('message', 'file_path')
        labels = {'message': 'message', 'file_path': 'Прикрепить файл'}
        widgets = {
            'message': forms.Textarea(attrs={
                'class': 'form-control m-0',
                'rows': 4,
                'placeholder': 'Напишите сообщение...'
            }),
        }

