from django.urls import path

from .views import *

urlpatterns = [
    path("", schedule_perspective, name='schedule_perspective'),
    path("search_program/", search_program, name='search_program'),
    path("update-program-position/", update_program_position, name='update-program-position'),
]