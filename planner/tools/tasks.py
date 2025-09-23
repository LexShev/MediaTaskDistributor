from celery import shared_task

from tools.ffprobe_scan import FfprobeScanner
from tools.update_no_material import get_no_material_list


@shared_task(bind=True, max_retries=3)
def process_video_task(self, program_id):
    try:
        scanner = FfprobeScanner(program_id)
        result = scanner.ffprobe_scan()
        return {
            'status': 'success',
            'program_id': program_id,
            'result': result
        }
    except Exception as exc:
        self.retry(exc=exc, countdown=60)

@shared_task(bind=True, max_retries=3)
def process_update_no_material(self):
    try:
        success_list, error_list = get_no_material_list()
        return {
            'status': 'success',
            'success_list': success_list,
            'error_list': error_list
        }
    except Exception as exc:
        self.retry(exc=exc, countdown=60)