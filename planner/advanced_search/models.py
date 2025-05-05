from django.db.models import Model, IntegerField


class AdvancedSearch(Model):
    owner = IntegerField('owner', primary_key=True, default=1)
    search_id = IntegerField()
