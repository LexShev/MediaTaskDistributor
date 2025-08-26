from django.urls import path
from .views import *


urlpatterns = [
    path("", task_manager, name="task_manager"),
    path("load_admin_task_table/", load_admin_task_table, name="load_admin_task_table"),
    path("sort_table/", sort_table, name="sort_table"),
]