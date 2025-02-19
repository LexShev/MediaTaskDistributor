import os
from ffmpeg import FFmpeg
import json
import datetime

start = datetime.datetime.now()
print('start:', start, '\n')

def ffmpeg_scan(file_path):
    parent_directory = os.path.dirname(os.path.abspath(__file__))
    parent_directory = r'C:\Users\a.shevchenko.st14\PycharmProjects\Viewing_planner\planner'
    ffprobe_directory = os.path.join(parent_directory, r'ffmpeg\bin\ffprobe.exe')
    ffprobe = FFmpeg(executable=ffprobe_directory).input(
        file_path,
        print_format="json",  # ffprobe will output the results in JSON format
        show_streams=None,
        show_format=None,
    )

    media = ffprobe.execute()
    print(json.loads(media))
    return json.loads(media)

end = datetime.datetime.now()
print('\nend:', end)
print('total:', end-start)