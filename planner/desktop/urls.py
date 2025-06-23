from django.urls import path
from .views import *

urlpatterns = [
    path("", show_desktop, name='desktop'),
    path("update_order/", update_order, name='update_order'),
    path("update_marker_name/", update_marker_name, name='update_marker_name'),
]