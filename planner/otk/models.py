from django.db.models import Model, Manager, IntegerField, TextField, DateField, CharField, TextChoices
from django.utils import timezone


class OtkModel(Model):
    owner = IntegerField('owner', primary_key=True, default=1)
    ready_date = DateField(default=None, null=True, blank=True)
    sched_date = DateField(default=None, null=True, blank=True)
    deadline = DateField(default=None, null=True, blank=True)
    worker_id = IntegerField(default=None, null=True, blank=True)
    material_type = CharField(default=None, max_length=50, null=True, blank=True)
    sched_id = IntegerField(default=None, null=True, blank=True)
    task_status = CharField(default=None, max_length=50, null=True, blank=True)

class TaskSearch(Model):
    owner = IntegerField('owner', primary_key=True, default=1)
    search_type = IntegerField(default=1)
    search_input = CharField(max_length=200, default=None, null=True, blank=True)
    sql_set = IntegerField(default=100)