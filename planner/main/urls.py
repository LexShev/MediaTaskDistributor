from django.urls import path
from .views import*

urlpatterns = [
    path("day", day),
    path("week", week),
    path("month", month),
    path("list", full_list),
    path("<int:id_card>", material_card),
    path("kpi_info", kpi_info),
]