import subprocess
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@dataclass
class CopyTaskResult:
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


class RcloneCopier:
    """Управление копированием через rclone"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self.base_cmd = ['rclone']
        if config_path:
            self.base_cmd.extend(['--config', config_path])

    def copy_with_progress(self, source: str, destination: str,
                           task_id: str, priority: str = 'normal') -> Tuple[bool, str, Dict]:
        cmd = self.base_cmd + [
            'copyto',
            source,
            destination,
            '--checksum',  # Проверка хэша после копирования
            '--progress',  # Прогресс
            '--stats', '10s',  # Статистика каждые 10 сек
            '--stats-one-line',  # Компактный формат для парсинга
            '--log-level', 'INFO',
            '--transfers', '1',  # Однопоточное копирование больших файлов
            '--buffer-size', '128M',  # Большой буфер для 5-30GB файлов
            '--multi-thread-streams', '4',  # Многопоточность внутри файла
            '--retries', '3',  # Внутренние ретраи rclone
            '--low-level-retries', '3',
            '--timeout', '30m',  # Таймаут операций
            '--contimeout', '1m',  # Таймаут соединения
        ]

        if not any(source.startswith(prefix) for prefix in ['s3:', 'gcs:', 'http']):
            cmd.extend(['--local-no-check-updated', '--no-traverse'])

        logger.info(f"[{task_id}] Starting rclone: {' '.join(cmd)}")

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        stats = {
            'transferred_gb': 0,
            'speed_mbps': 0,
            'progress_percent': 0,
            'errors': 0
        }

        # Читаем прогресс и сразу логируем
        for line in process.stderr:
            if 'Transferred:' in line:
                parts = line.split(',')
                for part in parts:
                    if 'GiB' in part and '/' in part:
                        transferred, total = part.strip().split('/')
                        stats['transferred_gb'] = float(transferred.strip().split()[0])
                    elif '%' in part:
                        stats['progress_percent'] = int(part.strip().replace('%', ''))
                    elif 'iB/s' in part:
                        speed = part.strip().split()[0]
                        stats['speed_mbps'] = float(speed)

                # Логируем прогресс — это попадёт в docker logs
                logger.info(
                    f"[{task_id}] Progress: {stats['progress_percent']}% | "
                    f"Speed: {stats['speed_mbps']} MB/s | "
                    f"Transferred: {stats['transferred_gb']} GB"
                )
            elif 'ERROR' in line or 'Failed' in line:
                logger.error(f"[{task_id}] rclone error: {line.strip()}")
                stats['errors'] += 1

        process.wait()

        if process.returncode == 0:
            logger.info(f"[{task_id}] Copy completed, verifying checksums...")
            source_hash = self._get_hash(source)
            dest_hash = self._get_hash(destination)
            stats['source_hash'] = source_hash
            stats['dest_hash'] = dest_hash

            if source_hash == dest_hash:
                logger.info(f"[{task_id}] Verification passed: {source_hash}")
                return True, "Copy verified", stats
            else:
                logger.error(
                    f"[{task_id}] Hash mismatch!\n"
                    f"  Source: {source_hash}\n"
                    f"  Dest:   {dest_hash}"
                )
                return False, "Hash mismatch after rclone", stats
        else:
            logger.error(f"[{task_id}] rclone failed with code {process.returncode}")
            return False, f"rclone failed with code {process.returncode}", stats

    def _get_hash(self, path: str) -> str:
        cmd = self.base_cmd + ['hashsum', 'MD5', path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip().split()[0]
        return ""


# Инициализация — экспортируем для импорта в tasks
rclone = RcloneCopier()