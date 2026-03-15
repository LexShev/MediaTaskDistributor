from django.urls import path

from .views import *

urlpatterns = [
    path("", playlist, name='playlist'),
    path("load_schedule_table/", load_schedule_table, name="load_schedule_table"),
    path("update_schedule_filter/", update_schedule_filter, name="update_schedule_filter"),
    path("get_schedule_list/", load_schedule_list, name="get_schedule_list"),
    path("update_playlist_status/", update_playlist_status, name="update_playlist_status"),
    path("update_playlist_comment/", update_playlist_comment, name="update_playlist_comment"),
    path("editors_notifications/", editors_notifications, name="editors_notifications"),

]