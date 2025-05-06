from django.urls import path
from .views import *


urlpatterns = [
    path("", common_pool, name="common_pool"),

]