import json
import logging
import os
import subprocess
from datetime import datetime

from django.db import connections

from planner.mongo_settings import mongo_connection
from planner.settings import OPLAN_DB, DEFAULT_LOG_DIR




def setup_logging():
    """Настройка логирования для консольного приложения"""
    os.makedirs(DEFAULT_LOG_DIR, exist_ok=True)
    log_file = os.path.join(DEFAULT_LOG_DIR, f"processing_log_{datetime.now().strftime('%Y-%m-%d')}.log")

    # Удаляем все старые обработчики
    logger = logging.getLogger('ffprobe_scanner')
    # Удаляем только наши обработчики, если они уже есть
    if logger.handlers:
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
    else:
        logger.setLevel(logging.INFO)

    # Настраиваем форматтер
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s",
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Файловый обработчик
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)

    # Обработчик для вывода в консоль
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    # Добавляем обработчики
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger


class FfprobeScanner:

    def __init__(self, file_id=None, file_path=None):
        self.file_id = file_id
        self.file_path = file_path
        self.ffprobe_file_path = None
        self.logger = setup_logging()

    # def get_file_id(self):
    #     try:
    #         with connections[OPLAN_DB].cursor() as cursor:
    #             query = f'''
    #                 SELECT Files.[FileID], Files.[Name]
    #                 FROM [{OPLAN_DB}].[dbo].[File] AS Files
    #                 JOIN [{OPLAN_DB}].[dbo].[Clip] AS Clips
    #                     ON Files.[ClipID] = Clips.[ClipID]
    #                 JOIN [{OPLAN_DB}].[dbo].[program] AS Progs
    #                     ON Clips.[MaterialID] = Progs.[SuitableMaterialForScheduleID]
    #                 WHERE Files.[Deleted] = 0
    #                 AND Files.[PhysicallyDeleted] = 0
    #                 AND Clips.[Deleted] = 0
    #                 AND Progs.[deleted] = 0
    #                 AND Progs.[DeletedIncludeParent] = 0
    #                 AND Progs.[program_id] = {self.program_id}
    #                 '''
    #
    #             cursor.execute(query)
    #             result = cursor.fetchone()
    #             if result:
    #                 self.file_id, self.file_path = result
    #                 self.ffprobe_file_path = self.file_path.replace('\\', '/').replace('//192.168.80.3', '/mnt').replace('//192.168.80.5', '/mnt')
    #                 return True
    #             else:
    #                 self.logger.warning(f"Файл для program_id {self.program_id} не найден в БД.")
    #                 return False
    #     except Exception as error:
    #         self.logger.error(f"Ошибка при запросе к БД: {error}")
    #         return False

    def ffprobe_scan(self):
        if not self.file_id or not self.file_path:
            return None
        self.ffprobe_file_path = self.file_path.replace('\\', '/').replace('//192.168.80.3', '/mnt').replace('//192.168.80.5', '/mnt')

        command = [
            "ffprobe",
            "-hide_banner",
            "-loglevel", "quiet",
            "-i", f"{self.ffprobe_file_path}",
            "-print_format", "json",
            "-show_streams",
            "-show_format"
        ]
        try:
            setup_logging()
            self.logger.info(f"Processing: {self.ffprobe_file_path}")
            output = subprocess.check_output(
                command,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0,
                shell=False
            )
            ffprobe_info = json.loads(output)
            self.logger.info("FFprobe result: %s", json.dumps(ffprobe_info, indent=2))
            db_status = self._insert_to_db(ffprobe_info)
            return {
                'status': 'success',
                'ffprobe_info': ffprobe_info,
                'db_status': db_status,
                'file_processed': True
            }
        except Exception as error:
            self.logger.error(f"ERROR processing for {self.file_path}: {error}")
            raise
            # self.retry(exc=e, countdown=60)


    def _insert_to_db(self, ffprobe_info):
        ffprobe_info['_id'] = self.file_id
        ffprobe_info['file_path'] = self.file_path
        ffprobe_info['ffmpeg_scanners'] = {}
        try:
            with mongo_connection('ffmpeg') as collection:
                collection.insert_one(ffprobe_info)
                self.logger.info(f"Data was added in DB successfully: {self.ffprobe_file_path}")
                return {'status': 'success', 'message': 'Data inserted successfully'}
        except Exception as e:
            self.logger.error(f"Error data writing in MongoDB for file_id: {self.file_id}, file_path: {self.ffprobe_file_path}: {e}")
            return {'status': 'error', 'message': str(e)}

