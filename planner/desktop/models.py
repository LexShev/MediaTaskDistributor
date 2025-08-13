from django.db.models import Model, IntegerField, CharField, DateTimeField


class ModelDeskTopFilter(Model):
    owner = IntegerField('owner', primary_key=True, default=1)
    schedules = CharField(max_length=100)
    material_type = CharField(max_length=100)
    work_dates = CharField(max_length=100)
    task_status = CharField(max_length=100)

class ModelCardsContainer(Model):
    container = IntegerField(default=1)
    owner = IntegerField(default=1)
    program_id = IntegerField(default=0)
    order = IntegerField(default=0)
    timestamp = DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (('owner', 'program_id'),)

class ModelListNames(Model):
    owner = IntegerField(default=1)
    list_id = IntegerField(default=1)
    name = CharField(max_length=30, default='Без названия')
