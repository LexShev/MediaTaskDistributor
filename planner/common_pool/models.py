from django.db.models import Model, IntegerField


class CommonPool(Model):
    owner = IntegerField('owner', primary_key=True, default=1)
    search_type = IntegerField(default=1)
    sql_set = IntegerField(default=100)
