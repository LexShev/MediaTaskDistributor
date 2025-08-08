from django.urls import path
from .views import *

urlpatterns = [
    path("", home, name='home'),
    path('load_calendar_info/', load_calendar_info, name='load_calendar_info'),
    path("update_total_unread_count/", update_total_unread_count, name='update_total_unread_count'),
    path("load_daily_kpi_chart/", load_daily_kpi_chart, name='load_daily_kpi_chart'),
    path("load_kpi_chart/", load_kpi_chart, name='load_kpi_chart'),
]