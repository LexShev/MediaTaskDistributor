from django.urls import path
from .views import *

urlpatterns = [
    path("day/", day),
    path("week/", week),
    path("week/<int:work_year>/<int:work_week>", week_date),
    path("list/", full_list, name='list'),
    path("<int:program_id>/", material_card),
    path("kpi_info/", kpi_info),
    path("worker/<int:worker_id>/", engineer_profile),
    path("work_calendar/", work_calendar),
    path("work_calendar/<int:cal_year>/", work_year_calendar),

    path("check_lock_card/<int:program_id>/", check_lock_card, name='check_lock_card'),
    path("block_card/<int:program_id>/<int:worker_id>/", block_card, name='block_card'),
    path("unblock_card/<int:program_id>/<int:worker_id>/", unblock_card, name='unblock_card'),
    path("get_worker_name/<int:worker_id>/", get_worker_name, name='get_worker_name'),

    path("load_cenz_data/", load_cenz_data, name='load_cenz_data'),
    path("submit_cenz_data/", submit_cenz_data, name='submit_cenz_data'),

    path("get_movie_poster/", get_movie_poster, name='get_movie_poster'),

    path("status_ready/", status_ready, name='status_ready'),
    path("ask_fix/", ask_fix, name='ask_fix'),
    path("cenz_info_change/", cenz_info_change, name='cenz_info_change'),

    path("cenz_batch/", cenz_batch, name='cenz_batch'),
]
