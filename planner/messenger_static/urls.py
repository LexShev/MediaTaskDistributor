from django.urls import path
from .views import *

urlpatterns = [
    path("", index, name='messenger_index'),
    path("<int:program_id>/", messenger, name='messenger'),
    path("notifications/", notificator, name='notifications'),
    path("read_message/", read_message, name='read_message'),
    path("read_notice/", read_notice, name='read_notice'),
    path("send_notice/", send_notice, name='send_notice'),

]