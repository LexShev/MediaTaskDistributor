from django.urls import path
from .views import *

urlpatterns = [
    path("", playlist, name='playlist'),
    path("load_schedule_table/", load_schedule_table, name="load_schedule_table"),
    path("update_playlist_values/", update_playlist_values, name="update_playlist_values"),

]