from django.db.models import Model, IntegerField, CharField


class AdvancedSearch(Model):
    owner = IntegerField('owner', primary_key=True, default=1)
    search_id = IntegerField(default=1)
    engineers = IntegerField(default=0)
    sql_set = IntegerField(default=0)
