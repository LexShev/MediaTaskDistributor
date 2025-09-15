from celery import shared_task

from tools.ffprobe_scan import FfprobeScanner


@shared_task(bind=True, max_retries=3)
def process_video_task(self, program_id):
    try:
        scanner = FfprobeScanner(program_id)
        scanner.ffprobe_scan()
    except Exception as exc:
        self.retry(exc=exc, countdown=60)