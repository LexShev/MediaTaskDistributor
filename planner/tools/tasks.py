from celery import shared_task

from tools.ffmpeg_scan import R128Scanner
from tools.ffprobe_scan import FfprobeScanner
# from tools.update_no_material import get_no_material_list


@shared_task(bind=True, max_retries=3, name='ffprobe_scan')
def process_ffprobe_scan(self, file_id, file_path):
    try:
        scanner = FfprobeScanner(file_id, file_path)
        return scanner.ffprobe_scan()
    except Exception as exc:
        self.retry(exc=exc, countdown=60)

@shared_task(bind=True, max_retries=3, name='r128_scan')
def process_r128_scan(self, file_id, file_path):
    try:
        scanner = R128Scanner(file_id, file_path)
        return scanner.r128_scan()
    except Exception as exc:
        self.retry(exc=exc, countdown=60)

# @shared_task(bind=True, max_retries=3)
# def process_update_no_material(self):
#     try:
#         success_list, error_list = get_no_material_list()
#         return {
#             'status': 'success',
#             'success_list': success_list,
#             'error_list': error_list
#         }
#     except Exception as exc:
#         self.retry(exc=exc, countdown=60)