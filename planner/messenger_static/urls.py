from django.urls import path
from .views import *

urlpatterns = [
    path("", index, name='messenger_index'),
    path("<int:program_id>/", messenger, name='messenger'),

]