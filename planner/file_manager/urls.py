from django.urls import path
from .views import *

urlpatterns = [
    path("", file_manager, name='file_manager'),
    path("load/", load_file_manager, name='load_file_manager'),
    path('retry/', retry_file_copy, name='retry_file_copy'),
    path('cancel/', cancel_copy_task, name='cancel_copy_task'),
]