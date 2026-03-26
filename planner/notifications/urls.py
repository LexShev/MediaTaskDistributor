from django.urls import path
from .views import *

urlpatterns = [
    path("notification_create/", notification_create, name='notification_create'),
    path("mark_notification_as_read/", mark_notification_as_read, name='mark_notification_as_read'),

]