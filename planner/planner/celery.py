import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'planner.celery_settings')

app = Celery('planner')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(['tools', 'distribution', 'messenger_static'])