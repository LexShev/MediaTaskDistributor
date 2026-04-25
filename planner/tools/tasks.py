from datetime import datetime
from pathlib import Path
from typing import Dict, List

from celery import shared_task
from celery.utils.log import get_task_logger
from dataclasses import asdict

from tools.ffmpeg_scan import R128Scanner
from tools.ffprobe_scan import FfprobeScanner
from tools.rclone_copy import CopyTaskResult, rclone

logger = get_task_logger(__name__)

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

@shared_task(
    bind=True,
    max_retries=5,
    default_retry_delay=300,
    queue='file_copy',
    name='copy_large_file'
)
def copy_large_file(self, source: str, destination: str,
                    priority: str = 'normal', verify_only: bool = False) -> Dict:
    """
    Задача копирования большого файла через rclone.
    """
    task_id = self.request.id
    start_time = datetime.now()

    source_path = Path(source)
    if not source_path.exists():
        raise FileNotFoundError(f"Source file not found: {source}")

    file_size_gb = source_path.stat().st_size / (1024 ** 3)

    logger.info(
        f"[{task_id}] Starting copy task:\n"
        f"  Source: {source}\n"
        f"  Destination: {destination}\n"
        f"  Size: {file_size_gb:.2f} GB\n"
        f"  Priority: {priority}"
    )

    result = CopyTaskResult(
        task_id=task_id,
        source=source,
        destination=destination,
        file_size_gb=round(file_size_gb, 2),
        status='copying',
        started_at=start_time.isoformat()
    )

    try:
        Path(destination).parent.mkdir(parents=True, exist_ok=True)

        if not verify_only:
            success, message, stats = rclone.copy_with_progress(
                source, destination, task_id, priority
            )

            if not success:
                logger.error(f"[{task_id}] Copy failed: {message}")
                raise Exception(f"Copy failed: {message}")
        else:
            source_hash = rclone._get_hash(source)
            dest_hash = rclone._get_hash(destination)
            success = source_hash == dest_hash
            stats = {'source_hash': source_hash, 'dest_hash': dest_hash}
            if success:
                logger.info(f"[{task_id}] Verification passed")
            else:
                logger.error(f"[{task_id}] Verification failed")

        elapsed = (datetime.now() - start_time).total_seconds()
        result.status = 'success'
        result.completed_at = datetime.now().isoformat()
        result.speed_mbps = round(file_size_gb * 1024 / elapsed, 2) if elapsed > 0 else 0
        result.source_hash = stats.get('source_hash', '')
        result.dest_hash = stats.get('dest_hash', '')

        logger.info(
            f"[{task_id}] ✅ Copy successful:\n"
            f"  Time: {elapsed:.1f}s\n"
            f"  Speed: {result.speed_mbps:.1f} MB/s\n"
            f"  Size: {file_size_gb:.2f} GB\n"
            f"  Hash: {result.source_hash}"
        )

        return asdict(result)

    except Exception as exc:
        elapsed = (datetime.now() - start_time).total_seconds()
        result.status = 'failed'
        result.error = str(exc)
        result.retry_count = self.request.retries

        logger.error(
            f"[{task_id}] ❌ Copy failed (attempt {self.request.retries}/{self.max_retries}):\n"
            f"  Error: {exc}\n"
            f"  Time elapsed: {elapsed:.1f}s"
        )

        if 'connection' in str(exc).lower() or 'timeout' in str(exc).lower():
            logger.info(f"[{task_id}] Network error, retrying in 10 minutes...")
            raise self.retry(exc=exc, countdown=600)
        else:
            raise self.retry(exc=exc)


@shared_task(queue='file_copy', name='cleanup_old_files')
def cleanup_old_files(directory: str, days_old: int = 30,
                      exclude_patterns: List[str] = None) -> int:
    """Очистка старых файлов"""
    import subprocess

    cmd = ['rclone', 'delete', directory, '--min-age', f'{days_old}d']
    if exclude_patterns:
        for pattern in exclude_patterns:
            cmd.extend(['--exclude', pattern])

    logger.info(f"Cleanup dry run: {directory} (older than {days_old} days)")
    cmd_dry = cmd + ['--dry-run']
    result = subprocess.run(cmd_dry, capture_output=True, text=True)
    logger.info(f"Files to delete:\n{result.stdout}")

    cmd_run = cmd  # без --dry-run
    result = subprocess.run(cmd_run, capture_output=True, text=True)
    logger.info(f"Cleanup completed with code {result.returncode}")

    return result.returncode

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