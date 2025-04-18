from django.db.models import Model, Manager, IntegerField, TextField, DateField, CharField


class ModelFilter(Model):
    owner = IntegerField('owner', primary_key=True, default=1)
    schedules = CharField(max_length=100)
    engineers = CharField(max_length=100)
    material_type = CharField(max_length=100)
    work_dates = CharField(max_length=100)
    task_status = CharField(max_length=100)


# class ProgramCustomFields(Model):
# owner	channels	workers	material_type	work_dates	task_status
# 1	['2', '3', '4', '5', '6', '7', '8', '9', '10', '12']	['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10']	['film', 'season']	2025-03-10	['not_ready', 'ready', 'fix']
