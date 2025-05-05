from django.db.models import Model, IntegerField, CharField


class ModelFilter(Model):
    owner = IntegerField('owner', primary_key=True, default=1)
    schedules = CharField(max_length=100)
    engineers = CharField(max_length=100)
    material_type = CharField(max_length=100)
    work_dates = CharField(max_length=100)
    task_status = CharField(max_length=100)

