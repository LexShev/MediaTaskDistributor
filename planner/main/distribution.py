from datetime import datetime, timedelta, date

from django.db import connections
from .db_connection import oplan_material_list


def main_distribution():
    # work_date = datetime.today().date()
    work_date = date(day=10, month=3, year=2025)
    dates = tuple(str(work_date + timedelta(days=day)) for day in range(23))
    columns = [('Progs', 'program_id'), ('Progs', 'parent_id'), ('SchedDay', 'schedule_id'),
               ('Progs', 'program_type_id'), ('Progs', 'name'), ('Progs', 'production_year'),
               ('Progs', 'AnonsCaption'), ('Progs', 'episode_num'),
               ('Progs', 'duration'), ('Files', 'Name'), ('SchedDay', 'day_date'),
               ('Task', 'engineer_id'), ('Task', 'sched_id'), ('Task', 'sched_date'),
               ('Task', 'work_date'), ('Task', 'task_status'), ('Task', 'file_path')]
    material_list_sql, django_columns = oplan_material_list(columns=columns, dates=dates)
    program_id_list = []
    for program_info in material_list_sql:
        if not program_info:
            continue
        program_id = program_info[0]
        if program_id in program_id_list:
            continue
        temp_dict = dict(zip(django_columns, program_info))
        sched_id = temp_dict.get('SchedDay_schedule_id')
        # if sched_id in (11, 20):
        #     print(temp_dict.get('Progs_program_id'), temp_dict.get('Files_Name'))
        sched_date = temp_dict.get('SchedDay_day_date')
        program_type_id = temp_dict.get('Progs_program_type_id')
        duration = temp_dict.get('Progs_duration')
        file_path = temp_dict.get('Files_Name')
        distribution_by_id(program_id, duration, sched_id, sched_date, work_date, program_type_id, file_path)
        program_id_list.append(program_id)


def distribution_by_id(program_id, duration, sched_id, sched_date, work_date, program_type_id, file_path):
    # !work_date продумать начало проверки
    planner_engineer_id = planner_engineer(program_id)
    oplan3_engineer_id = oplan3_engineer(program_id)
    if sched_id in (11, 20):
        print(program_id, sched_id, file_path)
    if program_type_id in (4, 5, 6, 10, 11, 12) and oplan3_engineer_id != 0 and not oplan3_engineer_id:

        if planner_engineer_id != 0 and not planner_engineer_id:
            status = 'not_ready'
            engineer_id, kpi, work_date = date_seek(work_date)
            insert_film(program_id, engineer_id, duration, sched_id, sched_date, work_date, status, file_path)
        else:
            # print('skip', program_id)
            # ? update(program_id, engineer_id, duration, date, status)
            engineer_id = planner_engineer_id
            status = 'not_ready'
    else:
        # ?
        engineer_id = oplan3_engineer_id
        status = 'ready'
    return engineer_id, status, work_date

# def kpi_min(date):
#     with connections['planner'].cursor() as cursor:
#         query = f'''SELECT
#         Worker.[worker_id], Worker.[worker], COALESCE(SUM(Task.[duration])/720000.0, 0) AS KPI
#         FROM [planner].[dbo].[worker_list] AS Worker
#         LEFT JOIN [planner].[dbo].[task_list] AS Task
#             ON Worker.[worker_id] = Task.[worker_id]
#             AND Task.[work_date] = '{date.strftime('%Y-%m-%d')}'
#         WHERE Worker.[holidays] != '{date.strftime('%Y-%m-%d')}'
#         AND Worker.[fired] = 'False'
#         GROUP BY Worker.[worker_id], Worker.[worker]'''
#         cursor.execute(query)
#         kpi_list = cursor.fetchall()
#         kpi_asc_list = sorted(kpi_list, key=lambda x: x[2])
#         # min(kpi_list, key=lambda x: x[2])
#         print('kpi_asc_list for date', date, '\n', kpi_asc_list)
#     return kpi_asc_list

def date_seek(work_date):
    kpi_info = kpi_min(work_date)
    if kpi_info and kpi_info[0][1] < 1:
        engineer_id, kpi = kpi_info[0]
        return engineer_id, kpi, work_date
    else:
        print('work_date', work_date)
        work_date += timedelta(days=1)
        return date_seek(work_date)

def kpi_min(work_date):
    kpi_list = []
    with connections['planner'].cursor() as cursor:
        query_01 = f'''
        SELECT [worker_id]
        FROM [planner].[dbo].[worker_list]
        WHERE '{work_date}' NOT IN (SELECT day_off FROM [planner].[dbo].[days_off])
        AND [fired] = 'False'
        '''
        cursor.execute(query_01)
        engineer_list = cursor.fetchall()

        if engineer_list:
            for engineer_id in engineer_list:
                engineer_id = engineer_id[0]
                query_02 = f'''
                SELECT Task.[engineer_id], Task.[duration]
                FROM [planner].[dbo].[task_list] AS Task
                WHERE Task.[work_date] = '{work_date}'
                AND Task.[engineer_id] = '{engineer_id}'
                '''
                cursor.execute(query_02)
                kpi = sum([args[1] for args in cursor.fetchall()])/720000.0
                kpi_list.append((engineer_id, kpi))
    return sorted(kpi_list, key=lambda x: x[1])

def insert_film(program_id, engineer_id, duration, sched_id, sched_date, work_date, task_status, file_path):
    with connections['planner'].cursor() as cursor:
        columns = '[program_id], [engineer_id], [duration], [sched_id], [sched_date], [work_date], [task_status], [file_path]'
        values = (program_id, engineer_id, duration, sched_id, sched_date, work_date, task_status, file_path)
        query = f'''
        INSERT INTO [planner].[dbo].[task_list] ({columns})
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        '''
        cursor.execute(query, values)
        # print(f'{program_id}, {engineer_id} successfully added')

def planner_engineer(program_id):
    with connections['planner'].cursor() as cursor:
        query_planner = f'''
        SELECT engineer_id
        FROM [planner].[dbo].[task_list]
        WHERE [program_id] = {program_id}'''
        cursor.execute(query_planner)
        planner_engineer_id = cursor.fetchone()
        if planner_engineer_id:
            return planner_engineer_id[0]
        else:
            return None

def oplan3_engineer(program_id):
    with connections['oplan3'].cursor() as cursor:
        query_oplan3 = f'''
        SELECT [IntValue]
        FROM [oplan3].[dbo].[ProgramCustomFieldValues] 
        WHERE [ObjectId] = {program_id}
        AND [ProgramCustomFieldId] = 15
        '''
        cursor.execute(query_oplan3)
        oplan3_engineer_id = cursor.fetchone()
        if oplan3_engineer_id:
            return oplan3_engineer_id[0]

