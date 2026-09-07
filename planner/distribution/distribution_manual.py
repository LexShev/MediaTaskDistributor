from datetime import date, timedelta

from django.db import connections
from planner.settings import OPLAN_DB, PLANNER_DB
from tools.ffmpeg_processing import start_ffmpeg_scanners


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

def oplan_material_list(program_id_list):
    if len(program_id_list) == 1:
        program_id_list = (program_id_list[0], program_id_list[0])
    else:
        program_id_list = tuple(program_id_list)
    print('program_id_list', program_id_list, type(program_id_list))
    print(type(program_id_list[0]))

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
            LEFT JOIN [{OPLAN_DB}].[dbo].[scheduled_program] AS SchedProg
                ON Progs.[program_id] = SchedProg.[program_id]
            LEFT JOIN [{OPLAN_DB}].[dbo].[schedule_day] AS SchedDay
                ON SchedProg.[schedule_day_id] = SchedDay.[schedule_day_id]
            WHERE Progs.[deleted] = 0
            AND Progs.[DeletedIncludeParent] = 0
            AND Progs.[program_id] IN {program_id_list}
            ORDER BY SchedProg.[DateTime] ASC
            '''
        cursor.execute(query)
        return [dict(zip(django_columns, material)) for material in cursor.fetchall()]

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
        WHERE Eng.[is_active] = 1
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

def start_distribution(program_id_list):
    material_list = oplan_material_list(program_id_list)
    success_list = []
    error_list = []
    start_distribution_date = date.today() + timedelta(days=1)
    for program_info in material_list:
        program_id = program_info.get('Progs_program_id')
        sched_id = program_info.get('SchedDay_schedule_id', 99)
        if sched_id is None:
            sched_id = 99
        progs_name = program_info.get('Progs_name')
        sched_date = program_info.get('SchedDay_day_date')
        duration = program_info.get('Progs_duration')
        suitable_material = program_info.get('Progs_SuitableMaterialForScheduleID')
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