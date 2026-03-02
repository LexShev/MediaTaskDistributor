from django.db.models import Model, IntegerField, DateTimeField, CharField


class PlaylistModel(Model):
    owner = IntegerField('owner', primary_key=True, default=0)
    schedule_date = CharField(max_length=100, default='', null=True, blank=True)
    schedule_id = IntegerField(default=None, null=True, blank=True)

class Comment(Model):
    schedule_day_id = IntegerField(primary_key=True, default=0)
    comment = CharField(max_length=200, default='', null=True, blank=True)
    last_edit_user_id = IntegerField(null=True, blank=True)
    last_edit_time = DateTimeField(auto_now_add=True, null=True, blank=True)

class Status(Model):
    schedule_day_id = IntegerField(primary_key=True, default=0)
    status = CharField(max_length=50, default='not_ready', null=True, blank=True)
    last_edit_user_id = IntegerField(null=True, blank=True)
    last_edit_time = DateTimeField(auto_now_add=True, null=True, blank=True)
