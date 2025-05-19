from django.db.models import Model, IntegerField, CharField, AutoField, FileField, DateTimeField, TextField

def get_upload_path(instance, filename):
    # Файл сохранится в: MEDIA_ROOT/attached_files/<program_id>/<filename>
    return f'attached_files/{instance.program_id}/{filename}'


class ModelFilter(Model):
    owner = IntegerField('owner', primary_key=True, default=1)
    schedules = CharField(max_length=100)
    engineers = CharField(max_length=100)
    material_type = CharField(max_length=100)
    work_dates = CharField(max_length=100)
    task_status = CharField(max_length=100)

class AttachedFiles(Model):
    owner = IntegerField(default=1)
    program_id = IntegerField(default=0)
    description = TextField(blank=True, null=True)
    timestamp = DateTimeField(auto_now_add=True)
    file_path = FileField(upload_to=get_upload_path, blank=True, null=True)