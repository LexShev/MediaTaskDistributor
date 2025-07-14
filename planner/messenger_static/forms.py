from django import forms
from django.core.exceptions import ValidationError

from .models import Message


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

class MessageForm(forms.ModelForm):
    file_path = forms.FileField(
        required=False,
        validators=[validate_file_type],
        widget=forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*, video/*, audio/*, .pdf, .doc, .docx, .srt'
            })
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

# class NotificationForm(forms.ModelForm):
#     class Meta:
#         model = Message
#         fields = ('notification',)
#         labels = {'notification': 'notification',}
#         widgets = {
#             'notification': forms.Textarea(attrs={
#                 'class': 'form-control m-0',
#                 'rows': 4,
#                 'placeholder': 'Напишите сообщение...'
#             }),
#         }