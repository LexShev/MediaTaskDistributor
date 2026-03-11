from django.urls import path
from .views import *

urlpatterns = [
    path("notification_create/", notification_create, name='notification_create'),

]