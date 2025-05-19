from django.urls import path
from .views import *

urlpatterns = [
    path("", index, name='home'),
    path('home_calendar/', home_calendar, name='home_calendar'),
    path("day", day),
    path("week", week),
    path("week/<int:work_year>/<int:work_week>", week_date),
    path("list", full_list),
    path("<int:program_id>", material_card),
    path("kpi_info", kpi_info),
    path("worker/<int:engineer_id>", engineer_profile),
    path("test_page", test_page),
    path("work_calendar/", work_calendar),
    path("work_calendar/<int:cal_year>", work_year_calendar),
    path("unblock_card/<int:program_id>/<int:worker_id>", unblock_card, name='unblock_card'),
    # redirect('name-of-my-view-pattern')
]