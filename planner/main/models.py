from django.db.models import Model, IntegerField, CharField, FileField, DateTimeField, TextField


def get_upload_path(instance, filename):
    return f'attached_files/{instance.program_id}/{filename}'

class ModelFilter(Model):
    owner = IntegerField('owner', primary_key=True, default=1)
    schedules = CharField(max_length=100)
    workers = CharField(max_length=100)
    material_type = CharField(max_length=100)
    work_dates = CharField(max_length=100)
    task_status = CharField(max_length=100)

class AttachedFiles(Model):
    owner = IntegerField(default=1)
    program_id = IntegerField(default=0)
    description = TextField(blank=True, null=True)
    timestamp = DateTimeField(auto_now_add=True)
    file_path = FileField(upload_to=get_upload_path, blank=True, null=True)

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
        ordering = ['timestamp']

class ModelSorting(Model):
    owner = IntegerField(default=1)
    user_order = TextField(default='sched_date')
    order_type = TextField(default='ASC')