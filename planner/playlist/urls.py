from django.urls import path

from .views import *

urlpatterns = [
    path("", playlist, name='playlist'),
    path("load_schedule_table/", load_schedule_table, name="load_schedule_table"),
    path("update_schedule_filter/", update_schedule_filter, name="update_schedule_filter"),
    path("get_schedule_day_table/", open_schedule_day_table, name="get_schedule_day_table"),

]