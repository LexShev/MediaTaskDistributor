from django.db.models import Model, Manager, IntegerField, TextField, DateField


class ModelFilter(Model):
    owner = IntegerField('owner', primary_key=True, default=1)
    # channels = TextField(blank=True)
    channels = TextField()
    engineers = TextField()
    material_type = TextField()
    work_dates = TextField()
    task_status = TextField()


# class ProgramCustomFields(Model):
# owner	channels	workers	material_type	work_dates	task_status
# 1	['2', '3', '4', '5', '6', '7', '8', '9', '10', '12']	['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10']	['film', 'season']	2025-03-10	['not_ready', 'ready', 'fix']
