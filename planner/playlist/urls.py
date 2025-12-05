from django.urls import path
from .views import *

urlpatterns = [
    path("", playlist, name='playlist'),
    path("load_schedule_table/", load_schedule_table, name="load_schedule_table"),
    path("update_schedule_filter/", update_schedule_filter, name="update_schedule_filter"),
    path("open_sched_day_table/", open_sched_day_table, name="open_sched_day_table"),

]