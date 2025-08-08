import hashlib
import json
import subprocess

from main.ffmpeg_info import mongo_connection


def ffmpeg_scan(file_path):
    command = [
        "ffprobe",
        "-hide_banner",
        "-loglevel", "quiet",
        "-i", f"{file_path}",
        "-print_format", "json",
        "-show_streams",
        "-show_format"
    ]

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
    scan_result = update_scan_result(file_path, ffprobe_info)
    print('scan_result', scan_result)
    # insert_db(scan_result)


def update_scan_result(file_path, ffprobe_info):
    ffprobe_info['_id'] = hashlib.md5(file_path.encode('utf-8')).hexdigest()
    ffprobe_info['file_path'] = file_path
    ffprobe_info['ffmpeg_scanners'] = {}
    return ffprobe_info


def insert_db(ffprobe_info):
    try:
        with mongo_connection('ffmpeg') as collection:
            collection.insert_one(ffprobe_info)
    except Exception as e:
        print(e)