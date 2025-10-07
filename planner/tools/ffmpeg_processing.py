from tools.tasks import process_ffprobe_scan, process_r128_scan
from planner.mongo_settings import mongo_connection


def start_ffmpeg_scanners(file_id, file_path):
    try:
        with mongo_connection('ffmpeg') as collection:
            ffmpeg_info = collection.find_one({'_id': file_id})
            if not ffmpeg_info:
                process_ffprobe_scan.delay(file_id=file_id, file_path=file_path)
            if not ffmpeg_info.get('ffmpeg_scanners'):
                process_r128_scan.delay(file_id=file_id, file_path=file_path)
    except Exception as error:
        print(error)