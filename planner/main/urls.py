from django.urls import path
from .views import *

urlpatterns = [
    path("", home, name='home'),
    path('load_calendar_info/', load_calendar_info, name='load_calendar_info'),
    path("day/", day),
    path("week/", week),
    path("week/<int:work_year>/<int:work_week>", week_date),
    path("list/", full_list, name='list'),
    path("<int:program_id>/", material_card),
    path("kpi_info/", kpi_info),
    path("worker/<int:engineer_id>/", engineer_profile),
    path("test_page/", test_page),
    path("work_calendar/", work_calendar),
    path("work_calendar/<int:cal_year>/", work_year_calendar),

    path("check_lock_card/<int:program_id>/", check_lock_card, name='check_lock_card'),
    path("block_card/<int:program_id>/<int:worker_id>/", block_card, name='block_card'),
    path("unblock_card/<int:program_id>/<int:worker_id>/", unblock_card, name='unblock_card'),
    path("get_worker_name/<int:worker_id>/", get_worker_name, name='get_worker_name'),

    path("load_cenz_data/", load_cenz_data, name='load_cenz_data'),
    path("submit_cenz_data/", submit_cenz_data, name='submit_cenz_data'),

    path("get_movie_poster/", get_movie_poster, name='get_movie_poster'),
    path("update_total_unread_count/", update_total_unread_count, name='update_total_unread_count'),
    path("load_daily_kpi_chart/", load_daily_kpi_chart, name='load_daily_kpi_chart'),
    path("load_kpi_chart/", load_kpi_chart, name='load_kpi_chart'),
]