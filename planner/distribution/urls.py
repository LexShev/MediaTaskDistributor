from django.urls import path
from .views import *


urlpatterns = [
    path('start_distribution/', start_distribution, name='start_distribution'),

]