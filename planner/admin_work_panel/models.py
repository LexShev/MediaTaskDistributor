from django.db.models import Model, Manager, IntegerField, TextField, DateField, CharField, TextChoices
from django.utils import timezone


class AdminModel(Model):
    owner = IntegerField('owner', primary_key=True, default=1)
    ready_date = DateField(default=timezone.now, null=True, blank=True)
    sched_date = DateField(default=timezone.now, null=True, blank=True)
    deadline = DateField(default=timezone.now, null=True, blank=True)
    engineer_id = IntegerField(default=1, null=True, blank=True)
    material_type = CharField(max_length=50, null=True, blank=True, default='film')
    sched_id = IntegerField(default=1, null=True, blank=True)
    task_status = CharField(max_length=50, null=True, blank=True, default='ready')

class TaskSearch(Model):
    owner = IntegerField('owner', primary_key=True, default=1)
    search_type = IntegerField(default=1)
    sql_set = IntegerField(default=100)