from django.db import connections
import pymongo
from django.template.defaulttags import register

conn = pymongo.MongoClient("localhost", 27017)
db = conn['planner_db']
collection = db['mediainfo']

@register.filter
def convert_fps(data):
    try:
        fps = eval(data)
        unit = 'fps'
        if fps % 1 == 0:
            data = f'{int(fps)} {unit}'
        else:
            data = f'{round(fps, 3)} {unit}'
    except ZeroDivisionError:
        data = '0'
    return data

@register.filter
def convert_khz(data):
    try:
        val = f'{float(data) / 1000} kHz'
        return val
    except Exception:
        pass

@register.filter
def convert_bytes(size, unit="bit/s"):
    if size:
        size = int(size)
        power = (2 ** 10)
        n = 0
        labels = ['', 'K', 'M', 'G', 'T']
        while size > power:
            size /= power
            n += 1
        return f'{round(size, 2)} {labels[n]}{unit}'

@register.filter
def convert_sec_to_time(sec, fps=25):
    if sec:
        sec = float(sec)
        hh = int(sec // 3600)
        mm = int((sec % 3600) // 60)
        ss = int((sec % 3600) % 60 // 1)
        ff = int(sec % 1 * fps)
        return f'{hh:02}:{mm:02}:{ss:02}.{ff:02}'


# @register.filter
# def convert_sec_to_time(sec):
#     return datetime.timedelta(seconds=float(sec))

@register.filter
def get_value(dictionary, key):
    return dictionary.get(key)


def ffmpeg_dict(program_id):
    cursor = collection.find({'_id': program_id})
    for record in cursor:
        return record