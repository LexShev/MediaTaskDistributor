from django.db import models
from django.db.models import IntegerField


class Message(models.Model):
    owner = IntegerField(default=1)
    program_id = IntegerField(default=0)
    content = models.TextField(blank=True, null=True)
    read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to='chat_files/%Y/%m/%d/', blank=True, null=True)

    @property
    def is_file(self):
        return bool(self.file)

    @property
    def file_type(self):
        if self.file:
            ext = self.file.name.split('.')[-1].lower()
            if ext in ['jpg', 'jpeg', 'png', 'gif']:
                return 'image'
            elif ext in ['mp4', 'mov', 'avi']:
                return 'video'
            elif ext in ['mp3', 'wav', 'aac']:
                return 'audio'
            else:
                return 'document'
        return None

    class Meta:
        ordering = ['timestamp']