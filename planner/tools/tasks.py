import os
from celery import shared_task
from celery.utils.log import get_task_logger
from django.utils import timezone

from file_manager.models import FileCopyTask
from tools.ffmpeg_scan import R128Scanner
from tools.ffprobe_scan import FfprobeScanner
from tools.rclone_copy import rclone

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional


logger = get_task_logger(__name__)

# from tools.update_no_material import get_no_material_list

def handle_copy_progress(task_id, stats_data: dict):
    """
    Обработчик прогресса копирования.
    Вызывается из RcloneCopier для обновления БД и отправки WebSocket.
    """
    # Определяем статус: если проверка хэшей - 'verifying', иначе 'copying'
    current_status = 'verifying' if stats_data.get('is_verifying') else 'copying'

    update_task_progress(
        task_id,
        status=current_status,
        progress=stats_data.get('progress_percent', 0),
        speed_mbps=stats_data.get('speed_mbps', 0),
        transferred_gb=stats_data.get('transferred_gb', 0),
        file_size_gb=stats_data.get('total_size_gb', 0),
    )

def update_task_progress(task_id, **kwargs):
    """Обновляет прогресс задачи в БД. НИКОГДА не бросает исключений."""
    try:
        task = FileCopyTask.objects.get(celery_task_id=task_id)

        # Обновляем поля
        updated_fields = []
        for key, value in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, value)
                updated_fields.append(key)

        if updated_fields:
            task.save(update_fields=updated_fields)
            logger.info(f"[{task_id}] DB updated: {', '.join(updated_fields)}")

        # WebSocket - опционально
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync

            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    "file_manager_updates",
                    {
                        "type": "file_progress_update",
                        "task_id": task.id,
                        'user_id': task.owner_id,
                        "celery_task_id": task_id,
                        "status": task.status,
                        "progress": task.progress or 0,
                        "speed_mbps": task.speed_mbps or 0,
                        "transferred_gb": task.transferred_gb or 0,
                        "file_size_gb": task.file_size_gb or 0,
                        "error_message": task.error_message,
                    }
                )
                # (считаем активные и ошибочные задачи)
                async_to_sync(channel_layer.group_send)(
                    "file_manager_updates",
                    {
                        "type": "file_manager_status_update",
                        'user_id': task.owner_id,
                        "active_count": FileCopyTask.objects.filter(
                            status__in=['pending', 'copying', 'verifying']
                        ).count(),
                        "error_count": FileCopyTask.objects.filter(
                            status='error'
                        ).count(),
                    }
                )
            else:
                logger.warning(f"[{task_id}] No channel layer!")
        except ImportError as e:
            logger.warning(f"[{task_id}] Channels not installed: {e}")
        except Exception as ws_error:
            logger.error(f"WebSocket skipped: {ws_error}")

    except FileCopyTask.DoesNotExist:
        logger.error(f"[{task_id}] FileCopyTask not found in DB!")
    except Exception as e:
        logger.error(f"[{task_id}] CRITICAL: Cannot update DB: {e}", exc_info=True)

@dataclass
class CopyTaskResult:
    """Результат задачи копирования"""
    task_id: str
    source: str
    destination: str
    file_size_gb: float
    status: str  # 'pending', 'copying', 'verifying', 'success', 'failed'
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    speed_mbps: Optional[float] = None
    source_hash: Optional[str] = None
    dest_hash: Optional[str] = None
    retry_count: int = 0
    error: Optional[str] = None

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
    name='copy_large_file'
)
def copy_large_file(
        self,
        source: str,
        destination: str,
        file_id: Optional[str] = None,
        priority: str = 'normal',
        verify_only: bool = False,
        user_id: int = None,
) -> Dict:
    task_id = self.request.id
    file_name = os.path.basename(source)

    # Получаем размер файла заранее
    try:
        file_size_bytes = os.path.getsize(source)
        file_size_gb = file_size_bytes / (1024 ** 3)
        logger.info(f"[{task_id}] File size: {file_size_gb:.2f} GB")
    except:
        file_size_bytes = 0
        file_size_gb = 0
        logger.warning(f"[{task_id}] Cannot determine file size")

    # Создаем запись в БД
    try:
        db_task, created = FileCopyTask.objects.update_or_create(
            celery_task_id=task_id,
            defaults={
                'status': 'pending',
                'file_path': source,
                'file_name': file_name,
                'destination_path': destination,
                'file_id': file_id,
                'priority': priority,
                'file_size_gb': file_size_gb,
                'started_at': timezone.now(),
            }
        )
        logger.warning(f"db_task: {db_task}, created: {created}")
        if user_id and created:
            try:
                db_task.owner_id = user_id
                db_task.save(update_fields=['owner'])
            except Exception:
                pass

        # отправляем WebSocket о новой задаче
        # if created:
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    'file_manager_updates',
                    {
                        'type': 'new_task_created',
                        'task_id': db_task.id,
                        'user_id': db_task.owner_id,
                        'celery_task_id': task_id,
                        'file_name': file_name,
                        'status': 'pending',
                        'progress': 0,
                        'speed_mbps': 0,
                        'transferred_gb': 0,
                        'file_size_gb': file_size_gb,
                    }
                )
                logger.info(f"[{task_id}] WebSocket: new task notified")
        except Exception as ws_err:
            logger.warning(f"[{task_id}] WebSocket new_task error: {ws_err}")

    except Exception as e:
        logger.error(f"[{task_id}] Failed to create DB record: {e}")

    logger.info(f"[{task_id}] Starting copy: {file_name}")

    try:
        # Обновляем статус на copying
        update_task_progress(task_id, status='copying', started_at=timezone.now())

        # Копирование

        def progress_callback(stats_data):
            # Определяем статус: если проверка хэшей - 'verifying', иначе 'copying'
            current_status = 'verifying' if stats_data.get('is_verifying') else 'copying'

            update_task_progress(
                task_id,
                status=current_status,
                progress=stats_data.get('progress_percent', 0),
                speed_mbps=stats_data.get('speed_mbps', 0),
                transferred_gb=stats_data.get('transferred_gb', 0),
                file_size_gb=stats_data.get('total_size_gb', 0),
            )

        success, message, stats = rclone.copy_with_progress_monitoring(
            source,
            destination,
            task_id,
            progress_callback,
            known_file_size_gb=file_size_gb
        )


        if success:
            if stats.get('already_exists'):
                comment = 'Файл уже существует (проверена контрольная сумма)'
            else:
                comment = 'Копирование успешно завершено'

            # Обновляем file_size_gb реальным значением, если rclone не вернул размер
            if not stats.get('total_size_gb') and file_size_gb:
                stats['total_size_gb'] = file_size_gb

            update_task_progress(
                task_id,
                status='completed',
                progress=100.0,
                completed_at=timezone.now(),
                file_size_gb=stats.get('total_size_gb'),
                speed_mbps=0,
                comment=comment
            )

            # уведомление пользователю ---
            # TODO:

            logger.info(f"[{task_id}] Copy completed")
            return {'status': 'success', 'task_id': task_id}
        else:
            update_task_progress(
                task_id,
                status='error',
                speed_mbps=0,
                completed_at=timezone.now(),
                error_message=message,
                comment=f'Ошибка копирования: {message}'
            )
            logger.error(f"[{task_id}] Copy failed: {message}")
            return {'status': 'error', 'task_id': task_id, 'message': message}

    except Exception as exc:
        # ВАЖНО: сначала обновляем статус в БД, потом ретрай
        logger.error(f"[{task_id}] Exception: {exc}", exc_info=True)
        retry_count = self.request.retries

        # Всегда записываем ошибку в БД
        error_msg = str(exc)[:500]

        if retry_count < self.max_retries - 1:
            # Есть ещё попытки
            update_task_progress(
                task_id,
                retry_count=retry_count + 1,
                error_message=error_msg,
                speed_mbps=0,
                comment=f'Повторная попытка {retry_count + 1}/{self.max_retries}'
            )
            # Теперь ретрай
            raise self.retry(exc=exc, countdown=60 * (retry_count + 1))
        else:
            # Попытки кончились
            update_task_progress(
                task_id,
                status='error',
                completed_at=timezone.now(),
                error_message=error_msg,
                comment=f'Ошибка после {self.max_retries} попыток'
            )
            return {'status': 'error', 'task_id': task_id, 'message': error_msg}


@shared_task(name='cleanup_old_files')
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