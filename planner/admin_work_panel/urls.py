from django.urls import path
from .views import *


urlpatterns = [
    path("", task_manager, name="task_manager"),

]