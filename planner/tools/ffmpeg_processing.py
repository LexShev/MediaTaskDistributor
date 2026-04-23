from tools.tasks import process_ffprobe_scan, process_r128_scan
from planner.mongo_settings import mongo_connection


def start_ffmpeg_scanners(file_id, file_path, ffmpeg_info):
    try:
        if not ffmpeg_info:
            print('ffmpeg info not found. Starting ffprobe_scan.')
            process_ffprobe_scan.delay(file_id=file_id, file_path=file_path)
        if not ffmpeg_info.get('ffmpeg_scanners'):
            process_r128_scan.delay(file_id=file_id, file_path=file_path)
    except Exception as error:
        print(error)