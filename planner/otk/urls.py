from django.urls import path
from .views import *

urlpatterns = [
    path("", otk, name='otk'),
    path("load_otk_task_table/", load_otk_task_table, name="load_otk_task_table"),

]