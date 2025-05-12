from django.urls import path
from .views import *

urlpatterns = [
    path("", report, name='report'),
    path("<int:cal_year>/<int:cal_month>", report_date),

]