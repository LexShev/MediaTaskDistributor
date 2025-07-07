from django.urls import path
from .views import *


urlpatterns = [
    path("common_pool/", common_pool, name="common_pool"),
    path('total-count/', total_count, name='total_count'),
    path('film-stats/', film_stats, name='film_stats'),
    path('season-stats/', season_stats, name='season_stats'),
    path('load_pool_table/', load_pool_table, name='load_pool_table'),
]