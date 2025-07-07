from django.urls import path
from .views import *

urlpatterns = [
    path("login_worker/", login_worker, name='login_worker'),
    path("logout_worker/", logout_worker, name='logout_worker'),

]