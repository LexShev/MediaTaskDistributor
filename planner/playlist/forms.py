from django import forms

from playlist.models import PlaylistModel


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