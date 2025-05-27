from django.template.defaulttags import register
from django.db import connections
import os

from main.settings.main_set import MainSettings


@register.filter
def cenz_name(cenz_id):
    if cenz_id:
        cenz_id = int(cenz_id)
    cenz_dict = {
        0: '0+',
        1: '6+',
        2: '12+',
        3: '16+',
        4: '18+'
    }
    return cenz_dict.get(cenz_id, '')

@register.filter
def engineer_name(engineer_id):
    if engineer_id:
        engineer_id = int(engineer_id)
    engineer_dict = {
        0: 'Александр Кисляков',
        1: 'Ольга Кузовкина',
        2: 'Дмитрий Гатенян',
        3: 'Мария Сучкова',
        4: 'Андрей Антипин',
        5: 'Роман Рогачев',
        6: 'Анастасия Чебакова',
        7: 'Никита Кузаков',
        8: 'Олег Кашежев',
        9: 'Марфа Тарусина',
        10: 'Евгений Доманов',
        11: 'Алексей Шевченко'
    }
    return engineer_dict.get(engineer_id, 'Не назначен')

@register.filter
def worker_name(worker_id):
    if worker_id:
        with connections['oplan3'].cursor() as cursor:
            query = f'SELECT [user_name] FROM [oplan3].[dbo].[user] WHERE [user_id] = {worker_id}'
            cursor.execute(query)
            worker = cursor.fetchone()
            if worker:
                return worker[0]
            else:
                return 'Аноним'
    else:
        return ''

@register.filter
def fields_name(field_id):
    if field_id:
        field_id = int(field_id)
    fields_dict = {
        5: 'Краткое описание',
        7: 'Дата отсмотра',
        8: 'ЛГБТ',
        9: 'Сигареты',
        10: 'Обнаженка',
        11: 'Наркотики',
        12: 'Мат',
        13: 'Другое',
        14: 'Ценз отсмотра',
        15: 'Тайтл проверил',
        16: 'Редакторские замечания',
        17: 'Meta',
        18: 'Теги',
        19: 'Иноагент'}
    return fields_dict.get(field_id)

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

@register.filter
def convert_frames_to_time(frames, fps=25):
    sec = int(frames) / fps
    yy = int((sec // 3600) // 24) // 365
    dd = int((sec // 3600) // 24) % 365
    hh = int((sec // 3600) % 24)
    mm = int((sec % 3600) // 60)
    ss = int((sec % 3600) % 60 // 1)
    ff = int(sec % 1 * fps)
    tf = f'{hh:02}:{mm:02}:{ss:02}.{ff:02}'
    if yy < 1:
        if dd < 1:
            return f'{hh:02}:{mm:02}:{ss:02}'
        else:
            return f'{dd:02}д. {hh:02}:{mm:02}:{ss:02}'
    else:
        if 0 < yy % 10 < 5:
            return f'{yy:02}г. {dd:02}д. {hh:02}:{mm:02}:{ss:02}'
        else:
            return f'{yy:02}л. {dd:02}д. {hh:02}:{mm:02}:{ss:02}'

@register.filter
def file_name(full_path):
    if full_path:
        return os.path.basename(full_path)
    else:
        return '-'

@register.filter
def dir_name(full_path):
    if full_path:
        return os.path.dirname(full_path).replace('\\\\192.168.80.3\\', "")
    else:
        return '-'

@register.filter
def dir_no_host_name(full_path):
    if full_path:
        return full_path.replace('\\\\192.168.80.3\\', "")

@register.filter
def schedule_name(schedule_id):
    schedules = {
        1: 'Общая задача',
        3: 'Крепкое',
        5: 'Планета дети',
        6: 'Мировой сериал',
        7: 'Мужской сериал',
        8: 'Наше детство',
        9: 'Романтичный сериал',
        10: 'Наше родное кино',
        11: 'Семейное кино',
        12: 'Советское родное кино',
        20: 'Кино +'
    }
    return schedules.get(schedule_id)

@register.filter
def month_name(cal_month):
    month_dict = {
        1: "Январь",
        2: "Февраль",
        3: "Март",
        4: "Апрель",
        5: "Май",
        6: "Июнь",
        7: "Июль",
        8: "Август",
        9: "Сентябрь",
        10: "Октябрь",
        11: "Ноябрь",
        12: "Декабрь"
    }
    return month_dict.get(cal_month)

@register.filter
def status_name(status):
    status_dict = MainSettings.status_dict
    return status_dict.get(status, '')

@register.filter
def thousands(num):
    return f'{num:,}'.replace(',', ' ')

@register.filter
def stringint(string):
    return int(string)

@register.filter
def basename(file_path):
    return os.path.basename(file_path)

@register.filter
def filename(file_path):
    return os.path.splitext(os.path.basename(file_path))[0]

@register.filter
def file_ext(file_path):
    return os.path.splitext(file_path)[-1].lower()