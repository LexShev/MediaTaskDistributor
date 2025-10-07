import json
import logging
import os
import subprocess
from datetime import datetime

from django.db import connections

from planner.mongo_settings import mongo_connection
from planner.settings import OPLAN_DB, DEFAULT_LOG_DIR, MEDIA_WAVEFORMS


def setup_logging():
    """Настройка логирования для консольного приложения"""
    os.makedirs(DEFAULT_LOG_DIR, exist_ok=True)
    log_file = os.path.join(DEFAULT_LOG_DIR, f"processing_log_{datetime.now().strftime('%Y-%m-%d')}.log")

    # Удаляем все старые обработчики
    logger = logging.getLogger('ffmpeg_scanner')
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

class R128Scanner:
    def __init__(self, file_id, file_path, r128_i=-23.0, r128_lra=11.0, r128_tp=-2.0):
        self.file_id, self.file_path = file_id, file_path
        self.ffmpeg_file_path = self.file_path.replace('\\', '/').replace('//192.168.80.3', '/mnt').replace('//192.168.80.5', '/mnt')
        self.image_file = os.path.join(MEDIA_WAVEFORMS, f'{self.file_id}.png')
        self.r128_i = r128_i
        self.r128_lra = r128_lra
        self.r128_tp = r128_tp
        self.logger = setup_logging()

    def db_scanners(self):
        try:
            with mongo_connection('ffmpeg') as collection:
                db_info = collection.find_one({'_id': self.file_id })
                if db_info and db_info.get('ffmpeg_scanners'):
                    return True
                else:
                    self.logger.error('file does not found in the database')
                    return False
        except Exception as error:
            self.logger.error(f"Database Error: {error}")
            return False


    def r128_scan(self):
        try:
            if not os.path.exists(self.ffmpeg_file_path):
                self.logger.error('file does not exist')
                return None

            if not self.db_scanners():
                self.logger.info("r128 scanning started")
                r128_scan_result = self.extract_loudnorm_data()
            else:
                self.logger.warning('scanning has already been done')
                r128_scan_result = {'status': 'error', 'message': 'scanning has already been done', 'file_processed': False}

            if not os.path.exists(self.image_file):
                self.logger.info("generating forms started")
                waveform_result = self.generate_waveforms()
            else:
                self.logger.warning('image file has already been existed')
                waveform_result = {'status': 'error', 'message': 'image file has already been existed', 'waveforms_created': False}

            self.logger.info("scanning has finished")
            return r128_scan_result, waveform_result

        except Exception as e:
            self.logger.error("Ошибка при обработке", e)
            raise

    def extract_loudnorm_data(self):
        try:
            command = [
                "ffmpeg",
                "-hide_banner",
                "-loglevel", "info",
                '-y',
                "-i", f"{self.ffmpeg_file_path}",
                "-af",
                f"loudnorm=I={self.r128_i}:LRA={self.r128_lra}:TP={self.r128_tp}:print_format=json",
                "-f", "null", "-",
            ]

            output = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0,
                shell=False
            )

            loudnorm_stats = []
            for line in output.stdout:
                if any(key in line for key in ['input_i', 'input_tp', 'input_lra', 'input_thresh']):
                    loudnorm_stats.append(line.replace(',', ''))

            if loudnorm_stats:
                loudnorm_dict = json.loads('{' + '\n,'.join(loudnorm_stats) + '}')
                self.logger.info("ffmpeg_scanners has been updated in the DB")
                db_status = self._insert_or_update_db({"ffmpeg_scanners": {'r128': loudnorm_dict}})
                return {
                    'status': 'success',
                    'r128_info': loudnorm_dict,
                    'file_processed': True
                }, db_status
            else:
                return {
                    'status': 'error',
                    'file_processed': False
                }, {}

        except subprocess.CalledProcessError as error:
            self.logger.error(f"ERROR processing for {self.file_path}: {error.stderr.decode('utf-8')}")
            raise Exception(f"ERROR processing for {self.file_path}: {error.stderr.decode('utf-8')}")
        except Exception as error:
            self.logger.error(f"ERROR processing for {self.file_path}: {error}")
            raise

    def generate_waveforms(self):
        try:
            command = [
                "ffmpeg",
                "-hide_banner",
                "-loglevel", "info",
                '-y',
                "-i", f"{self.ffmpeg_file_path}",
                "-filter_complex", "showwavespic=s=2000x800:scale=cbrt:draw=full",
                "-frames:v", '1',
                self.image_file
            ]
            subprocess.check_output(
                command,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                encoding='utf-8',
                errors='replace',
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0,
                shell=False
            )
            if os.path.exists(self.image_file):
                self._insert_or_update_db({'waveforms': True})
                self._insert_or_update_db({'file_path': self.file_path})
                return {'status': 'success', 'waveforms_created': True, 'message': 'file does not exist'}
            else:
                return {'status': 'error', 'waveforms_created': False}
        except Exception as e:
            self.logger.error(f"Error data writing in MongoDB for file_id: {self.file_id}, file_path: {self.ffmpeg_file_path}: {e}")
            return {'status': 'error', 'waveforms_created': False, 'message': str(e)}

    def _insert_or_update_db(self, updated_dict):
        try:
            with mongo_connection('ffmpeg') as collection:
                collection.update_one({'_id': self.file_id}, {"$set": updated_dict}, upsert=True)
                return {'status': 'success', 'message': 'database updated'}
        except Exception as e:
            self.logger.error(f"Error data writing in MongoDB for file_id: {self.file_id}, file_path: {self.ffmpeg_file_path}: {e}")
            return {'status': 'error', 'message': str(e)}