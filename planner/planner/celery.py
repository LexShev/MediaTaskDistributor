import os
from celery import Celery
from kombu import Queue, Exchange

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'planner.celery_settings')

app = Celery('planner')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Определяем очереди
app.conf.task_queues = (
    Queue('celery', Exchange('celery'), routing_key='celery', queue_arguments={'x-max-priority': 10}),
    Queue('file_copy', Exchange('file_copy'), routing_key='file_copy', queue_arguments={'x-max-priority': 10}),
)

# Маршрутизация задач по очередям
app.conf.task_routes = {
    'copy_large_file': {'queue': 'file_copy'},
    'cleanup_old_files': {'queue': 'file_copy'},
    # Все остальные задачи по умолчанию идут в 'celery'
}

app.conf.task_default_queue = 'celery'

# Дополнительные настройки для больших файлов
app.conf.task_acks_late = True  # Подтверждение после выполнения
app.conf.worker_prefetch_multiplier = 1  # Брать только 1 задачу (для file_copy воркера)
app.conf.task_time_limit = 7200  # 2 часа максимум
app.conf.task_soft_time_limit = 7000

app.autodiscover_tasks(['tools', 'distribution'])