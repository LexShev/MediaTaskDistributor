from datetime import datetime, date, timedelta
from decimal import Decimal
from pathlib import Path

from django.core.serializers.json import DjangoJSONEncoder


class CustomJSONEncoder(DjangoJSONEncoder):
    """Кастомный JSON encoder для обработки специальных типов данных"""

    def default(self, obj):
        # Преобразуем datetime в строку
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()

        # Преобразуем timedelta в строку или секунды
        if isinstance(obj, timedelta):
            return str(obj)  # или obj.total_seconds() если нужны секунды

        # Преобразуем Decimal в float
        if isinstance(obj, Decimal):
            return float(obj)

        # Преобразуем bytes в строку (если встречаются бинарные данные)
        if isinstance(obj, bytes):
            return obj.decode('utf-8', errors='ignore')

        # Обработка множеств (set)
        if isinstance(obj, set):
            return list(obj)

        # Обработка генераторов
        if hasattr(obj, '__iter__') and not isinstance(obj, (str, list, dict, tuple)):
            return list(obj)

        # Если объект имеет метод __dict__ (например, модели Django)
        if hasattr(obj, '__dict__'):
            return obj.__dict__

        # Если объект имеет метод to_json или similar
        if hasattr(obj, 'to_json'):
            return obj.to_json()

        # Для любых других объектов пробуем преобразовать в строку
        try:
            return str(obj)
        except Exception as error:
            print(error)
            # Если ничего не помогло, используем родительский метод
            return super().default(obj)

def normalize_path(file_path: str) -> str:
    """Преобразует Windows-путь в Linux-путь"""
    return (
        file_path
        .replace('\\', '/')           # Меняем слеши
        .replace('//', '/')           # Убираем двойные слеши
        .replace('192.168.80.3', 'mnt')
        .replace('192.168.80.5', 'mnt')
    )


def get_filename_only(windows_path: str) -> str:
    """
    Извлекает только имя файла из Windows-пути.

    Args:
        windows_path: \\192.168.80.5\ContentA\FILMS\F_Muppet Show_2026_LEP_1080p25_H264_10Mbps.mp4

    Returns:
        F_Muppet Show_2026_LEP_1080p25_H264_10Mbps.mp4
    """
    clean_path = windows_path.replace('\\', '/')
    return Path(clean_path).name