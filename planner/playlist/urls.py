from django.urls import path
from .views import *

urlpatterns = [
    path("", playlist, name='playlist'),

]