from django.urls import path

from . import views

urlpatterns = [
    path('program/<int:program_id>/', views.program_detail, name='planner_api_program'),
]
