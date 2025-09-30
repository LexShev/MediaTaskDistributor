from django.urls import path
from .views import *

urlpatterns = [
    path("", report),
    path("<int:cal_year>/<int:cal_month>", month_report),
    path("month/", month_report, name='month'),
    path("<int:cal_year>/<int:cal_month>/<int:cal_day>", date_report, name='date_report'),
    path("<int:cal_year>/<int:cal_month>/<int:cal_day>/<int:schedule_id>", date_report, name='date_schedules_report'),
    path("today/", today_report, name='today'),
    path('load_on_air_calendar_info/', load_on_air_calendar_info, name='load_on_air_calendar_info'),
    path('get_schedule_table/<str:sched_date>/<int:schedule_id>', get_schedule_table, name='get_schedule_table'),
    path('apply_final_batch/', apply_final_batch, name='apply_final_batch'),
    path('final_fail_batch/', final_fail_batch, name='final_fail_batch'),
    path('on_air_search/', on_air_search, name='on_air_search'),
    path('load_on_air_task_table/', load_on_air_task_table, name='load_on_air_task_table'),
]