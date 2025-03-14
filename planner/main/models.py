from django.db.models import Model, Manager, IntegerField, TextField, DateField


class MainFilter(Model):
    owner = IntegerField('owner', primary_key=True, default=1)
    # channels = TextField(blank=True)
    channels = TextField()
    workers = TextField()
    material_type = TextField()
    work_dates = DateField()
    task_status = TextField()


