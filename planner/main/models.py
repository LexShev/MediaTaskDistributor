from django.db import models

class ListFilter(models.Model):
    body = models.TextField()
    date = models.DateField()
    channels = models.TextField()
    workers = models.TextField()
    material_type = models.TextField()
    status = models.TextField()

