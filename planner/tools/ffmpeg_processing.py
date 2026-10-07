import threading

from tools.tasks import process_ffprobe_scan, process_r128_scan


def start_ffmpeg_scanners(file_id, file_path, ffmpeg_info=None):
    try:
        if not ffmpeg_info:
            print('ffmpeg info not found. Starting ffprobe_scan.')
            process_ffprobe_scan.delay(file_id=file_id, file_path=file_path)
        if not ffmpeg_info.get('ffmpeg_scanners'):
            process_r128_scan.delay(file_id=file_id, file_path=file_path)
    except Exception as error:
        print(error)


def _ensure_ffmpeg_scanners(file_id, file_path):
    """Читает данные из MongoDB и, если нужно, ставит задачи сканирования.

    Выполняется в фоновом потоке и никогда не должен ронять HTTP-запрос.
    """
    try:
        from main.ffmpeg_info import ffmpeg_dict
        ffmpeg_info = ffmpeg_dict(file_id)
        start_ffmpeg_scanners(file_id, file_path, ffmpeg_info)
    except Exception as error:
        print(error)


def ensure_ffmpeg_scanners_async(file_id, file_path):
    """Запускает проверку и постановку задач сканирования в daemon-потоке.

    Не блокирует ответ сервера при недоступных MongoDB/Redis.
    """
    if not file_id or not file_path:
        return
    threading.Thread(
        target=_ensure_ffmpeg_scanners,
        args=(file_id, file_path),
        daemon=True,
    ).start()
