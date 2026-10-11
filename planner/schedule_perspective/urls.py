from django.urls import path

from . import views

urlpatterns = [
    path('', views.schedule_perspective, name='schedule_perspective'),
    path('window/', views.api_window, name='schedule_perspective_window'),
    path('search/', views.api_search, name='schedule_perspective_search'),
    path('series/<int:kinopoisk_id>/structure/',
         views.api_series_structure, name='schedule_perspective_series_structure'),
    path('film-info/', views.api_film_info, name='schedule_perspective_film_info'),
    path('poster/', views.api_poster, name='schedule_perspective_poster'),
    path('slot/add/', views.api_slot_add, name='schedule_perspective_slot_add'),
    path('slot/move/', views.api_slot_move, name='schedule_perspective_slot_move'),
    path('slot/delete/', views.api_slot_delete, name='schedule_perspective_slot_delete'),
    path('day/<str:action>/', views.api_day_status, name='schedule_perspective_day_status'),
    path('downloads/generate/', views.api_generate_downloads,
         name='schedule_perspective_generate_downloads'),
]
