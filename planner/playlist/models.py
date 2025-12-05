from django.db.models import Model, IntegerField, DateField, CharField


class PlaylistModel(Model):
    owner = IntegerField('owner', primary_key=True, default=0)
    schedule_date = CharField(max_length=100, default='', null=True, blank=True)
    schedule_id = IntegerField(default=None, null=True, blank=True)

