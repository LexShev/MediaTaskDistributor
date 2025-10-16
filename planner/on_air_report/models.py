from django.db.models import Model, IntegerField, DateField, CharField, TextChoices, TextField


class OnAirModel(Model):
    owner = IntegerField('owner', primary_key=True, default=0)
    ready_dates = TextField(default='[]', null=True, blank=True)
    sched_dates = TextField(default='[]', null=True, blank=True)
    workers = TextField(default='[]', null=True, blank=True)
    material_type = TextField(default='[]', null=True, blank=True)
    schedules = TextField(default='[]', null=True, blank=True)
    task_status = TextField(default='[]', null=True, blank=True)
    order = TextField(default='progs_name', null=True, blank=True)
    order_type = TextField(default='ASC', null=True, blank=True)

class TaskSearch(Model):
    owner = IntegerField('owner', primary_key=True, default=1)
    search_type = IntegerField(default=2)
    search_input = CharField(max_length=200, default=None, null=True, blank=True)
    sql_set = IntegerField(default=100)