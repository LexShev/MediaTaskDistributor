from django import forms

from main.form_choices import choice
from playlist.models import PlaylistModel, EditorsNotificationFilter, EditorsNotificationTaskSearch


class PlaylistFilter(forms.ModelForm):
    class Meta:
        model = PlaylistModel
        fields = ('schedule_date',)
        labels = {
            'schedule_date': 'Даты эфира',
        }
        widgets = {
            'schedule_date': forms.DateInput(
                attrs={'class': 'form-control', 'data-bs-theme': 'light', 'type': 'text', 'id': 'schedule_date'}),
        }

class EditorsNotificationFilterForm(forms.ModelForm):
    class Meta:
        model = EditorsNotificationFilter
        fields = ('notification_time', 'worker_id', 'notification_type', 'sched_id', 'is_read')

        labels = {'notification_time': 'Время',
                  'worker_id': 'Сотрудник',
                  'notification_type': 'Категория',
                  'sched_id': 'Канал',
                  'is_read': 'Прочитано',
                  }

        widgets = {
            'notification_time': forms.DateInput(
                attrs={'class': 'form-control editors_notification_filter', 'type': 'date', 'id': "notification_time"}, format='%Y-%m-%d'),
            'worker_id': forms.Select(
                attrs={'class': "form-select editors_notification_filter", 'id': "worker_id"}, choices=choice.editors),
            'notification_type': forms.Select(
                attrs={'class': "form-select editors_notification_filter", 'id': "notification_type"}, choices=choice.notification_type),
            'sched_id': forms.Select(
                attrs={'class': "form-select editors_notification_filter", 'id': "sched_id"}, choices=choice.schedules),
            'is_read': forms.Select(
                attrs={'class': "form-select editors_notification_filter", 'id': "is_read"}, choices=choice.read_status),
        }

class EditorsNotificationTaskSearchForm(forms.ModelForm):
    class Meta:
        model = EditorsNotificationTaskSearch
        fields = ('search_input',)

        labels = {'search_input': 'Поиск'}

        widgets = {
            'search_input': forms.TextInput(
                attrs={'class': 'form-control', 'id': 'search_input', 'placeholder': 'начните вводить содержание уведомления ...'},
            ),
        }