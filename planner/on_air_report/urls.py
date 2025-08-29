from django.urls import path
from .views import *

urlpatterns = [
    path("", report, name='report'),
    path("<int:cal_year>/<int:cal_month>", month_report),
    path("<int:cal_year>/<int:cal_month>/<int:day>", report_date),
    path('load_on_air_calendar_info/', load_on_air_calendar_info, name='load_on_air_calendar_info'),

]