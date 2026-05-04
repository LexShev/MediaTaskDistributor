# planner/tools/rclone_copy.py
import os
import re
import subprocess
import threading
from typing import Optional, Callable
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


class RcloneCopier:
    """Управление копированием через rclone"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self.base_cmd = ['rclone']
        if config_path:
            self.base_cmd.extend(['--config', config_path])

    def copy_with_progress_monitoring(
            self,
            source: str,
            destination: str,
            task_id: str,
            progress_callback: Optional[Callable] = None
    ) -> tuple:
        """
        Копирование с мониторингом прогресса и callback.
        Rclone с --checksum сам проверяет хэши.
        """

        cmd = self.base_cmd + [
            'copyto',
            source,
            destination,
            '--checksum',          # Rclone сам проверит хэши после копирования
            '--progress',
            '--stats', '3s',
            '--log-level', 'INFO',
            '--stats-log-level', 'NOTICE',  # ← Выводить прогресс всегда
            '--transfers', '1',
            '--buffer-size', '128M',
            '--multi-thread-streams', '4',
            '--retries', '3',
            '--low-level-retries', '3',
            '--timeout', '30m',
            '--contimeout', '1m',
        ]

        if not any(source.startswith(prefix) for prefix in ['s3:', 'gcs:', 'http']):
            cmd.extend(['--local-no-check-updated', '--no-traverse'])

        logger.info(f"[{task_id}] Starting rclone: {' '.join(cmd)}")

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        stats = {
            'transferred_gb': 0,
            'total_size_gb': 0,
            'speed_mbps': 0,
            'progress_percent': 0,
            'errors': 0,
            'checks': 0,  # Количество проверок хэша
            'transfers': 0,  # Количество реальных передач
            'already_exists': False  # Файл уже существовал?
        }

        # Паттерн для парсинга строки прогресса rclone
        progress_patterns = [
            # Формат с GiB/MiB
            re.compile(
                r'Transferred:\s+([\d.]+)\s*([GMK]i?B?)\s*/\s*([\d.]+)\s*([GMK]i?B?).*?(\d+)%.*?([\d.]+)\s*([GMK]i?B?)/s',
                re.IGNORECASE
            ),
            # Формат с Bytes
            re.compile(
                r'Transferred:\s+([\d.]+)\s*(\w+?)\s*/\s*([\d.]+)\s*(\w+?).*?(\d+)%.*?([\d.]+)\s*(\w+?)/s',
                re.IGNORECASE
            ),
        ]
        checks_pattern = re.compile(r'Checks:\s+(\d+)\s*/\s*(\d+),\s*(\d+)%', re.IGNORECASE)
        transfers_pattern = re.compile(r'Transferred:\s+(\d+)\s*/\s*(\d+),\s*(\d+)%', re.IGNORECASE)

        def convert_to_gb(value, unit):
            """Конвертирует в GB"""
            unit = unit.upper().replace('I', '').strip()
            value = float(value)

            if unit.startswith('T'):
                return value * 1024
            elif unit.startswith('G'):
                return value
            elif unit.startswith('M'):
                return value / 1024
            elif unit.startswith('K'):
                return value / (1024 * 1024)
            elif unit.startswith('B'):
                return value / (1024 * 1024 * 1024)
            else:
                return value

        def convert_speed(value, unit):
            """Конвертирует в MB/s"""
            unit = unit.upper().replace('I', '').replace('/S', '').strip()
            value = float(value)

            if unit.startswith('G'):
                return value * 1024
            elif unit.startswith('M'):
                return value
            elif unit.startswith('K'):
                return value / 1024
            elif unit.startswith('B'):
                return value / (1024 * 1024)
            else:
                return value

        def read_output():
            logger.info(f"[{task_id}] Started reading rclone output...")
            line_count = 0

            for line in process.stdout:
                line = line.strip()
                line_count += 1

                logger.info(f"[{task_id}] RCLONE[{line_count}]: {line[:200]}")

                # Парсим Checks
                checks_match = checks_pattern.search(line)
                if checks_match:
                    stats['checks'] = int(checks_match.group(1))
                    # Если есть проверки и нет передач — файл уже существует
                    if stats['transfers'] == 0:
                        stats['already_exists'] = True
                        stats['progress_percent'] = 100

                        logger.info(f"[{task_id}] File already exists, verifying checksum...")

                        if progress_callback:
                            progress_callback(stats)

                # Парсим Transferred (счетчик файлов)
                transfers_match = transfers_pattern.search(line)
                if transfers_match and 'MiB' not in line and 'GiB' not in line:
                    stats['transfers'] = int(transfers_match.group(1))

                # Парсим прогресс (размер в MiB/GiB)
                for pattern in progress_patterns:
                    match = pattern.search(line)
                    if match:
                        try:
                            transferred_val = float(match.group(1))
                            transferred_unit = match.group(2)
                            total_val = float(match.group(3))
                            total_unit = match.group(4)
                            percent = int(match.group(5))
                            speed_val = float(match.group(6))
                            speed_unit = match.group(7)

                            stats['transferred_gb'] = convert_to_gb(transferred_val, transferred_unit)
                            stats['total_size_gb'] = convert_to_gb(total_val, total_unit)
                            stats['progress_percent'] = percent
                            stats['speed_mbps'] = convert_speed(speed_val, speed_unit)

                            logger.info(
                                f"[{task_id}] {percent}% | "
                                f"{stats['speed_mbps']:.1f} MB/s | "
                                f"{stats['transferred_gb']:.2f}/{stats['total_size_gb']:.2f} GB"
                            )

                            if progress_callback:
                                progress_callback(stats)
                            break
                        except Exception as e:
                            logger.error(f"[{task_id}] Parse error: {e}")

                if 'ERROR' in line.upper() or 'FAIL' in line.upper():
                    logger.error(f"[{task_id}] {line}")
                    stats['errors'] += 1

            logger.info(f"[{task_id}] Finished ({line_count} lines)")

        # Запускаем чтение в потоке
        output_thread = threading.Thread(target=read_output, daemon=True)
        output_thread.start()

        # Ждем завершения
        try:
            process.wait(timeout=3600)
        except subprocess.TimeoutExpired:
            process.kill()
            logger.error(f"[{task_id}] Timeout!")
            return False, "Timeout after 1 hour", stats

        output_thread.join(timeout=10)

        if process.returncode == 0:
            if stats['already_exists']:
                logger.info(f"[{task_id}] File already exists, checksum verified")
                return True, "File already exists (verified)", stats
            else:
                logger.info(f"[{task_id}] Copy verified")
                return True, "Copy verified", stats
        else:
            logger.error(f"[{task_id}] Failed with code {process.returncode}")
            return False, f"Failed with code {process.returncode}", stats


rclone = RcloneCopier()