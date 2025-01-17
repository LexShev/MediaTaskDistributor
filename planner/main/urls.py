from django.urls import path
from . import views

urlpatterns = [
    path("day", views.day),
    path("week", views.week),
    path("month", views.month),
]