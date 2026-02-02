import random
from datetime import datetime, timedelta, date
from typing import Dict

from django.db import connections
from planner.settings import OPLAN_DB, PLANNER_DB
from tools.ffmpeg_processing import start_ffmpeg_scanners

DEFAULT_PROGRAM_TYPES = (4, 5, 6, 10, 11, 12, 16)
DEFAULT_SCHEDULES_IDS = (3, 5, 6, 7, 8, 9, 10, 11, 12, 20)


def check_date(obj):
    if isinstance(obj, str):
        try:
            return datetime.strptime(obj, '%Y-%m-%d').date()
        except Exception as error:
            print(error)
            return date.today()
    elif isinstance(obj, (datetime, date)):
        return obj
    return date.today()

def main_distribution(distr_sched_end_date=None, distr_sched_id=None) -> Dict[str, str]:
    # work_date = datetime.today().date()

    # Дата начала сканирования сеток
    start_work_date = date.today()
    if distr_sched_end_date:
        distr_sched_end_date = check_date(distr_sched_end_date)
    else:
        distr_sched_end_date = date.today()

    work_duration = (distr_sched_end_date - start_work_date).days
    print('будет обработано', work_duration, 'дней')
    # С какой даты отдавать в работу
    start_distribution_date = date.today() + timedelta(days=1)

    if distr_sched_id:
        distr_sched_id = (distr_sched_id, distr_sched_id)
    else:
        distr_sched_id = DEFAULT_SCHEDULES_IDS
    # start_work_date = date(day=1, month=12, year=2025)
    # work_duration = 31*2

    # 3	Крепкое
    # 5	Планета дети
    # 6	Мировой сериал
    # 7	Мужской сериал
    # 8	Наше детство
    # 9	Романтичный сериал
    # 10	Наше родное кино
    # 11	Семейное кино
    # 12	Советское родное кино
    # 20	Кино +
    # 36	Кино Индии

    material_list_sql, django_columns = oplan_material_list(
        start_date=start_work_date,
        schedules_id=distr_sched_id,
        work_duration=work_duration
    )
    if not material_list_sql:
        return {'status': 'success', 'message': 'Нет новых задач для распределения',
                'success_list': [], 'error_list': []}
    program_id_list = []
    success_list = []
    error_list = []
    # Перемешиваем список
    random.shuffle(material_list_sql)
    for i, program_info in enumerate(material_list_sql, 1):
        if not program_info:
            continue
        program_id = program_info[0]
        if program_id in program_id_list:
            continue
        program_id_list.append(program_id)

        temp_dict = dict(zip(django_columns, program_info))

        sched_id = temp_dict.get('SchedDay_schedule_id')
        progs_name = temp_dict.get('Progs_name')
        sched_date = temp_dict.get('SchedDay_day_date')
        duration = temp_dict.get('Progs_duration')
        suitable_material = temp_dict.get('Progs_SuitableMaterialForScheduleID')
        worker_id, kpi, work_date = date_seek(start_distribution_date, duration)

        if suitable_material:
            file_id, file_path = find_file_path(program_id)
            status = 'not_ready'
            start_ffmpeg_scanners(file_id=file_id, file_path=file_path)
        else:
            file_id, file_path = '', ''
            status = 'no_material'
        rowcount = insert_film(program_id, worker_id, duration, sched_id, sched_date, work_date, status, file_path)
        if rowcount > 0:
            success_list.append({'program_id': program_id, 'progs_name': progs_name,
                                 'file_id': file_id, 'file_path': file_path, 'duration': duration,
                                 'worker_id': worker_id, 'sched_id': sched_id, 'sched_date': sched_date})
        else:
            error_list.append({'program_id': program_id, 'progs_name': progs_name,
                               'file_id': file_id, 'file_path': file_path, 'duration': duration,
                               'worker_id': worker_id, 'sched_id': sched_id, 'sched_date': sched_date})
    if not error_list:
        return {'status': 'success', 'message': 'Распределение успешно завершено без ошибок',
                'success_list': success_list, 'error_list': []}
    else:
        return {'status': 'error', 'message': 'Распределение завершено с ошибками',
                'success_list': success_list, 'error_list': error_list}


def oplan_material_list(start_date, work_duration, program_type=DEFAULT_PROGRAM_TYPES, schedules_id=DEFAULT_SCHEDULES_IDS):
    columns = [
        ('Progs', 'program_id'), ('Progs', 'parent_id'), ('SchedDay', 'schedule_id'), ('Progs', 'program_type_id'),
        ('Progs', 'name'), ('Progs', 'production_year'), ('Progs', 'AnonsCaption'), ('Progs', 'episode_num'),
        ('Progs', 'duration'), ('Progs', 'SuitableMaterialForScheduleID'), ('SchedDay', 'day_date'), ('SchedProg', 'DateTime')
    ]
    with connections[OPLAN_DB].cursor() as cursor:
        sql_columns = ', '.join([f'{col}.[{val}]' for col, val in columns])
        django_columns = [f'{col}_{val}' for col, val in columns]
        query = f'''
            SELECT DISTINCT {sql_columns}
            FROM [{OPLAN_DB}].[dbo].[program] AS Progs
            JOIN [{OPLAN_DB}].[dbo].[scheduled_program] AS SchedProg
                ON Progs.[program_id] = SchedProg.[program_id]
            JOIN [{OPLAN_DB}].[dbo].[schedule_day] AS SchedDay
                ON SchedProg.[schedule_day_id] = SchedDay.[schedule_day_id]
            JOIN [{OPLAN_DB}].[dbo].[schedule] AS Sched
                ON SchedDay.[schedule_id] = Sched.[schedule_id]
            LEFT JOIN [{PLANNER_DB}].[dbo].[task_list] AS Task
                ON Progs.[program_id] = Task.[program_id]
            WHERE Progs.[deleted] = 0
            AND Progs.[DeletedIncludeParent] = 0
            AND SchedProg.[Deleted] = 0
            AND SchedDay.[schedule_id] IN {schedules_id}
            AND SchedDay.[day_date] BETWEEN '{start_date}' AND DATEADD(DAY, {work_duration}, '{start_date}')
            AND Progs.[program_type_id] IN {program_type}
            AND Progs.[program_id] > 0
            AND Progs.[program_id] NOT IN
                (SELECT DISTINCT [ObjectId] FROM [{OPLAN_DB}].[dbo].[ProgramCustomFieldValues]
                WHERE [ProgramCustomFieldId] = 15
                OR [ProgramCustomFieldId] = 7)
            AND Progs.[program_id] NOT IN
                (SELECT [program_id] FROM [{PLANNER_DB}].[dbo].[task_list])
            AND Task.[worker_id] IS NULL
            ORDER BY SchedProg.[DateTime] ASC
            '''
        cursor.execute(query)
        material_list_sql = cursor.fetchall()
    return material_list_sql, django_columns

def find_file_path(program_id):
    try:
        with connections[OPLAN_DB].cursor() as cursor:
            query = f'''
            SELECT Files.[FileID], Files.[Name]
            FROM [{OPLAN_DB}].[dbo].[File] AS Files
            JOIN [{OPLAN_DB}].[dbo].[Clip] AS Clips
                ON Files.[ClipID] = Clips.[ClipID]
            JOIN [{OPLAN_DB}].[dbo].[program] AS Progs
                ON Clips.[MaterialID] = Progs.[SuitableMaterialForScheduleID]
            WHERE Files.[Deleted] = 0
            AND Files.[PhysicallyDeleted] = 0
            AND Clips.[Deleted] = 0
            AND Progs.[deleted] = 0
            AND Progs.[DeletedIncludeParent] = 0
            AND Progs.[program_id] = {program_id}
            '''
            cursor.execute(query)
            file_info = cursor.fetchone()
        if file_info and file_info[0]:
            return file_info
    except Exception as error:
        print(error)
    return None, None


def date_seek(work_date, duration):
    kpi_info = kpi_min(work_date)
    if kpi_info:
        for worker_id, kpi in kpi_info:
            new_kpi = kpi + (duration / 720000.0)
            if new_kpi <= 1:
                return worker_id, kpi, work_date
    print('work_date', work_date)
    work_date += timedelta(days=1)
    return date_seek(work_date, duration)

def kpi_min(work_date):
    with connections[PLANNER_DB].cursor() as cursor:
        query = f'''
        DECLARE @target_date DATE
        SET @target_date = %s
        SELECT
            Eng.[worker_id] AS worker_id,
            CASE
                WHEN Days.[day_off] IS NOT NULL THEN NULL
                WHEN Vac.[vacation_id] IS NOT NULL THEN NULL
                ELSE CAST(COALESCE(SUM(Task.[duration]), 0) AS FLOAT) / 720000.0
            END AS kpi
        FROM
            [{PLANNER_DB}].[dbo].[engineers_list] AS Eng
        LEFT JOIN [{PLANNER_DB}].[dbo].[task_list] AS Task
            ON Eng.[worker_id] = Task.[worker_id]
            AND Task.[work_date] = CONVERT(DATE, @target_date)
        LEFT JOIN [{PLANNER_DB}].[dbo].[days_off] AS Days
            ON Days.[day_off] = CONVERT(DATE, @target_date)
        LEFT JOIN [{PLANNER_DB}].[dbo].[vacation_schedule] AS Vac
            ON Eng.[worker_id] = Vac.[worker_id]
            AND CONVERT(DATE, @target_date) BETWEEN Vac.[start_date] AND Vac.[end_date]
        GROUP BY
            Eng.[worker_id],
            Days.[day_off],
            Vac.[vacation_id]
        ORDER BY
            kpi ASC;
        '''
        cursor.execute(query, (work_date,))
        res = cursor.fetchall()
        return sorted([item for item in res if item[1] is not None], key=lambda x: x[1])

def insert_film(program_id, worker_id, duration, sched_id, sched_date, work_date, task_status, file_path=''):
    try:
        with connections[PLANNER_DB].cursor() as cursor:
            columns = '[program_id], [worker_id], [duration], [sched_id], [sched_date], [work_date], [task_status], [file_path], [deadline]'
            values = (program_id, worker_id, duration, sched_id, sched_date, work_date, task_status, file_path, sched_date)
            query = f'''
            INSERT INTO [{PLANNER_DB}].[dbo].[task_list] ({columns})
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, DATEADD(DAY, -14, CAST(%s AS DATE)))
            '''
            cursor.execute(query, values)
            rowcount = cursor.rowcount
            print(rowcount)
            return rowcount
    except Exception as error:
        print(error)
        return 0
