from django.urls import path
from .views import *


urlpatterns = [
    path("update_no_material/", update_no_material, name='update_no_material'),

]