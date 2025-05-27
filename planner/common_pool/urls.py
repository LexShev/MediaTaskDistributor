from django.urls import path
from .views import *


urlpatterns = [
    path("common_pool/", common_pool, name="common_pool"),
    path('load_pool_table/', load_pool_table, name='load_pool_table'),
]