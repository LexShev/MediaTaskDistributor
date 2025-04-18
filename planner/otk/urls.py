from django.urls import path
from .views import *

urlpatterns = [
    path("", work_list, name='work_list'),

]