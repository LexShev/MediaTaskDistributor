from datetime import datetime, timedelta, date

from django.db import connections
from planner.settings import OPLAN_DB, PLANNER_DB


DEFAULT_PROGRAM_TYPES = (4, 5, 6, 10, 11, 12, 16)
DEFAULT_SCHEDULES_IDS = (3, 5, 6, 7, 8, 9, 10, 11, 12, 20)

def main_distribution():
    # work_date = datetime.today().date()
    work_date = date(day=1, month=11, year=2025)
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
    material_list_sql, django_columns = oplan_material_list(start_date=work_date, schedules_id=(3, 6, 7, 8, 9, 10, 11, 12), work_duration=30)
    # , schedules_id = (3, 5, 6, 7, 8, 9, 10, 11, 12)
    program_id_list = []
    for i, program_info in enumerate(material_list_sql, 1):
        if not program_info:
            continue
        program_id = program_info[0]
        if program_id in program_id_list:
            continue
        program_id_list.append(program_id)

        temp_dict = dict(zip(django_columns, program_info))

        sched_id = temp_dict.get('SchedDay_schedule_id')
        sched_date = temp_dict.get('SchedDay_day_date')
        duration = temp_dict.get('Progs_duration')
        suitable_material = temp_dict.get('Progs_SuitableMaterialForScheduleID')

        worker_id, kpi, work_date = date_seek(date(day=1, month=10, year=2025), duration)

        if suitable_material:
            file_path = find_file_path(program_id)
            status = 'not_ready'
        else:
            file_path = ''
            status = 'no_material'
        insert_film(program_id, worker_id, duration, sched_id, sched_date, work_date, status, file_path)
    return 'success'


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
    with connections[OPLAN_DB].cursor() as cursor:
        query = f'''
        SELECT Files.[Name]
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
        file_path = cursor.fetchone()
    if file_path:
        return file_path[0]
    return None


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
    with connections[PLANNER_DB].cursor() as cursor:
        columns = '[program_id], [worker_id], [duration], [sched_id], [sched_date], [work_date], [task_status], [file_path]'
        values = (program_id, worker_id, duration, sched_id, sched_date, work_date, task_status, file_path)
        query = f'''
        INSERT INTO [{PLANNER_DB}].[dbo].[task_list] ({columns})
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        '''
        cursor.execute(query, values)
        print(cursor.rowcount)
        # print(f'{program_id}, {worker_id} successfully added')

# def planner_engineer(program_id):
#     with connections[PLANNER_DB].cursor() as cursor:
#         query_planner = f'''
#         SELECT worker_id
#         FROM [{PLANNER_DB}].[dbo].[task_list]
#         WHERE [program_id] = {program_id}'''
#         cursor.execute(query_planner)
#         planner_worker_id = cursor.fetchone()
#         if planner_worker_id:
#             return planner_worker_id[0]
#         else:
#             return None
#
# def oplan3_engineer(program_id):
#     with connections[OPLAN_DB].cursor() as cursor:
#         query_oplan3 = f'''
#         SELECT [IntValue]
#         FROM [{OPLAN_DB}].[dbo].[ProgramCustomFieldValues]
#         WHERE [ObjectId] = {program_id}
#         AND [ProgramCustomFieldId] = 15
#         '''
#         cursor.execute(query_oplan3)
#         oplan3_engineer_id = cursor.fetchone()
#         if oplan3_engineer_id:
#             return oplan3_engineer_id[0]

