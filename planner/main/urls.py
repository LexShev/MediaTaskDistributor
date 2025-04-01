from django.urls import path
from .views import *

urlpatterns = [
    path("", index, name='home'),
    path("day", day),
    path("week", week),
    path("week/<int:work_year>/<int:work_week>", week_date),
    path("month", month, name='month'),
    path("month/<int:cal_year>/<int:cal_month>", month_date),
    path("list", full_list),
    path("<int:program_id>", material_card),
    path("kpi_info", kpi_info),
    path("workers/<int:engineer_id>", kpi_engineer),
    path("test_page", test_page),
    path("my_view", my_view),
    path("common_pool", common_pool),
    path("work_calendar/<int:cal_year>", work_calendar),
    path("distribution", distribution, name='distribution'),
]