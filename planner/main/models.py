from django.db import models

class MainFilter(models.Model):
    body = models.TextField()
    work_dates = models.DateField()
    channels = models.TextField()
    workers = models.TextField()
    material_type = models.TextField()
    task_status = models.TextField()

