from django.urls import path
from .views import *

urlpatterns = [
    path("fast_search", main_search, name='fast_search'),
    path("advanced_search", dop_search, name='advanced_search'),
]