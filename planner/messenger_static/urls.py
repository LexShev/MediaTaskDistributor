from django.urls import path
from .views import *

urlpatterns = [
    path("<int:program_id>", index, name='messenger'),

]