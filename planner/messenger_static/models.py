from django.db import models
from django.db.models import IntegerField, AutoField

class MessageViews(models.Model):
    message_id = IntegerField(default=0)
    worker_id = IntegerField(default=0)


class Program(models.Model):
    program_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    production_year = models.IntegerField()

    class Meta:
        managed = False  # Не управлять миграциями
        db_table = 'program'

class Message(models.Model):
    message_id = AutoField(primary_key=True)
    owner = IntegerField(default=1)
    program_id = IntegerField(default=0)
    message = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    file_path = models.FileField(upload_to='chat_files/%Y/%m/%d/', blank=True, null=True)

    @property
    def program(self):
        return Program.objects.using('oplan3').get(program_id=self.program_id)

    @property
    def is_file(self):
        return bool(self.file_path)

    @property
    def file_type(self):
        if self.file_path:
            ext = self.file_path.name.split('.')[-1].lower()
            if ext in ['jpg', 'jpeg', 'png', 'gif']:
                return 'image'
            elif ext in ['mp4', 'mov', 'avi']:
                return 'video'
            elif ext in ['mp3', 'wav', 'aac', 'ac3']:
                return 'audio'
            else:
                return 'document'
        return None

    class Meta:
        db_table = 'messenger_static_message'
        ordering = ['timestamp']