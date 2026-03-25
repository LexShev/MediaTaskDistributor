from django.db.models import Model, IntegerField, DateTimeField, CharField, DateField, BooleanField


class PlaylistModel(Model):
    owner = IntegerField('owner', primary_key=True, default=0)
    schedule_date = CharField(max_length=100, default='', null=True, blank=True)
    schedule_id = CharField(max_length=100, default='[]', null=True, blank=True)

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

class EditorsNotificationFilter(Model):
    owner = IntegerField('owner', primary_key=True, default=1)
    notification_time = DateField(default=None, null=True, blank=True)
    worker_id = IntegerField(default=None, null=True, blank=True)
    notification_type = CharField(default=None, max_length=50, null=True, blank=True)
    sched_id = IntegerField(default=None, null=True, blank=True)
    is_read = BooleanField(default=None, null=True, blank=True)

class EditorsNotificationTaskSearch(Model):
    owner = IntegerField('owner', primary_key=True, default=1)
    search_input = CharField(max_length=200, default=None, null=True, blank=True)
