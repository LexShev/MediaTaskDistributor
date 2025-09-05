import re

from django.template.defaulttags import register
from django.db import connections
import os

from main.settings.main_set import MainSettings
from planner.settings import OPLAN_DB, PLANNER_DB



@register.simple_tag
def is_active(request, url):
    if request.path.startswith(url):
        return "active"
    return ""

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
    if engineer_id or str(engineer_id) == '0' :
        with connections[OPLAN_DB].cursor() as cursor:
            query = f'SELECT [full_name] FROM [{PLANNER_DB}].[dbo].[engineers_list] WHERE [engineer_id] = %s'
            cursor.execute(query, (engineer_id,))
            engineer = cursor.fetchone()
            if engineer:
                return engineer[0]
            else:
                return 'Аноним'

    else:
        return ''

@register.filter
def worker_name(worker_id):
    if worker_id:
        with connections[OPLAN_DB].cursor() as cursor:
            query = f'SELECT [user_name] FROM [{OPLAN_DB}].[dbo].[user] WHERE [user_id] = %s'
            cursor.execute(query, (worker_id,))
            worker = cursor.fetchone()
            if worker:
                return worker[0]
            else:
                return 'Аноним'
    else:
        return ''

@register.filter
def planner_worker_username(worker_id):
    if worker_id:
        with connections[OPLAN_DB].cursor() as cursor:
            query = f'SELECT [username], [first_name], [last_name] FROM [{PLANNER_DB}].[dbo].[auth_user] WHERE [id] = %s'
            cursor.execute(query, (worker_id,))
            worker = cursor.fetchone()
            if worker:
                return worker[0]
            else:
                return 'Аноним'
    else:
        return ''

@register.filter
def planner_worker_name(worker_id):
    if worker_id:
        with connections[OPLAN_DB].cursor() as cursor:
            query = f'SELECT [username], [first_name], [last_name] FROM [{PLANNER_DB}].[dbo].[auth_user] WHERE [id] = %s'
            cursor.execute(query, (worker_id,))
            worker = cursor.fetchone()
            if worker:
                username, first_name, last_name = worker
                return f'{first_name} {last_name}'
            else:
                return 'Аноним'
    else:
        return ''

@register.filter
def engineer_id_to_worker_id(engineer_id) -> int:
    with connections[PLANNER_DB].cursor() as cursor:
        query = f'SELECT [worker_id] FROM [{PLANNER_DB}].[dbo].[engineers_list] WHERE [engineer_id] = %s'
        cursor.execute(query, (engineer_id,))
        worker = cursor.fetchone()
        if worker and worker[0]:
            return worker[0]
        else:
            return 0

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
        19: 'Иноагент'
    }
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
    except Exception as e:
        print(e)

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
    return ''


@register.filter
def convert_sec_to_time(sec, fps=25):
    if sec:
        sec = float(sec)
        hh = int(sec // 3600)
        mm = int((sec % 3600) // 60)
        ss = int((sec % 3600) % 60 // 1)
        ff = int(sec % 1 * fps)
        return f'{hh:02}:{mm:02}:{ss:02}.{ff:02}'
    return ''


# @register.filter
# def convert_sec_to_time(sec):
#     return datetime.timedelta(seconds=float(sec))

@register.filter
def get_value(dictionary, key):
    return dictionary.get(key)

@register.filter
def convert_frames_to_time(frames, fps=25):
    try:
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
    except Exception as e:
        print(e)
        return ''

@register.filter
def file_name(full_path):
    if full_path:
        return os.path.basename(full_path.replace('\\', '/').replace('//', '/'))
    else:
        return '-'

@register.filter
def dir_name(full_path):
    if full_path:
        dir_path = re.sub(r'^\\\\\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\\\\?', '', full_path)
        return os.path.dirname(dir_path.replace('\\', '/'))
    else:
        return '-'

@register.filter
def dir_no_host_name(full_path):
    if full_path:
        return full_path.replace('\\\\192.168.80.3\\', "")
    return ''


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
def status_color(status):
    color_dict = MainSettings.color_dict
    return color_dict.get(status, '')

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

@register.filter
def program_name(program_id):
    with connections[OPLAN_DB].cursor() as cursor:
        query = f'SELECT [name], [production_year] FROM [{OPLAN_DB}].[dbo].[program] WHERE [program_id] = %s'
        cursor.execute(query, (program_id,))
        res = cursor.fetchone()
        if res:
            name, production_year = res
            if name and production_year:
                return f'{name} ({production_year})'
            elif name:
                return name
            return ''
        else:
            return program_id

@register.filter
def desktop_visibility(task_status):
    if task_status in ('ready', 'otk', 'final'):
        return True
    return False
