from django.urls import path
from .views import *

urlpatterns = [
    path("", index, name='home'),
    path("day", day),
    path("week", week),
    path("week/<int:work_year>/<int:work_week>", week_date),
    path("month/<int:cal_year>/<int:cal_month>", month),
    path("list", full_list),
    path("<int:program_id>", material_card),
    path("kpi_info", kpi_info),
    path("workers/<int:worker_id>", kpi_worker),
    path("test_page", test_page),
    path("my_view", my_view),
    path("common_pool", common_pool),
    path("work_calendar/<int:cal_year>", work_calendar),
]