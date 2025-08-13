from django.db.models import Model, IntegerField, CharField


class CommonPool(Model):
    owner = IntegerField('owner', primary_key=True, default=1)
    search_type = IntegerField(default=1)
    search_input = CharField(max_length=200, default=None, null=True, blank=True)
    sql_set = IntegerField(default=100)

    class Meta:
        db_table = 'common_pool_commonpool'
