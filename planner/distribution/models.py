from datetime import date, timedelta

from django.db.models import Model, IntegerField, DateField


class Distribution(Model):
    owner = IntegerField(default=1)
    distr_sched_end_date = DateField(default=date.today() + timedelta(days=1))
    distr_sched_id = IntegerField(default=None, null=True, blank=True)