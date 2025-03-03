from django.urls import path
from .views import*

urlpatterns = [
    path("", index, name='home'),
    path("day", day),
    path("week", week),
    path("week/<str:start_day>", week_date),
    path("month", month),
    path("list", full_list),
    path("<int:program_id>", material_card),
    path("kpi_info", kpi_info),
    path("workers/<int:worker_id>", kpi_worker),
]