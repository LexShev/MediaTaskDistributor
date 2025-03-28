from datetime import datetime, timedelta, date
from django.db import connections
from .list_view import oplan_material_list


def main_distribution():
    work_date = datetime.today()
    work_date = date(day=10, month=3, year=2025)
    material_list_sql, django_columns = oplan_material_list(work_date=work_date, program_type=(4, 5, 6, 10, 11, 12))
    program_id_list = []
    for program_info in material_list_sql:
        if not program_info:
            continue
        program_id = program_info[0]
        if program_id in program_id_list:
            continue
        temp_dict = dict(zip(django_columns, program_info))
        program_type_id = temp_dict['Progs_program_type_id']
        duration = temp_dict['Progs_duration']
        distribution_by_id(work_date, program_id, program_type_id, duration)
        program_id_list.append(program_id)


def distribution_by_id(work_date, program_id, program_type_id, duration):
    # !work_date продумать начало проверки
    planner_worker_id = planner_cenz_worker(program_id)
    oplan3_worker_id = oplan3_cenz_worker(program_id)
    if program_type_id in (4, 5, 6, 10, 11, 12) and oplan3_worker_id != 0 and not oplan3_worker_id:
        if planner_worker_id != 0 and not planner_worker_id:
            status = 'not_ready'
            worker_id, kpi, work_date = date_seek(work_date)
            insert_film(program_id, worker_id, duration, work_date, status)
        else:
            # print('skip', program_id)
            # ? update(program_id, worker_id, duration, date, status)
            worker_id = planner_worker_id
            status = 'not_ready'
    else:
        # ?
        worker_id = oplan3_worker_id
        status = 'ready'
    return worker_id, status, work_date

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
        worker_id, kpi = kpi_info[0]
        return worker_id, kpi, work_date
    else:
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
        worker_list = cursor.fetchall()

        if worker_list:
            for worker_id in worker_list:
                worker_id = worker_id[0]
                query_02 = f'''
                SELECT Task.[worker_id], Task.[duration]
                FROM [planner].[dbo].[task_list] AS Task
                WHERE Task.[work_date] = '{work_date}'
                AND Task.[worker_id] = '{worker_id}'
                '''
                cursor.execute(query_02)
                kpi = sum([args[1] for args in cursor.fetchall()])/720000.0
                kpi_list.append((worker_id, kpi))
    return sorted(kpi_list, key=lambda x: x[1])

def insert_film(program_id, worker_id, duration, work_date, status):
    with connections['planner'].cursor() as cursor:
        columns = '[program_id], [worker_id], [duration], [work_date], [task_status]'
        query = f'''
        INSERT INTO [planner].[dbo].[task_list] ({columns})
        VALUES ({program_id}, {worker_id}, {duration}, '{work_date}', '{status}')
        '''
        cursor.execute(query)
        print(f'{program_id}, {worker_id} successfully added')

def planner_cenz_worker(program_id):
    with connections['planner'].cursor() as cursor:
        query_planner = f'''
        SELECT worker_id
        FROM [planner].[dbo].[task_list]
        WHERE [program_id] = {program_id}'''
        cursor.execute(query_planner)
        planner_worker_id = cursor.fetchone()
        if planner_worker_id:
            return planner_worker_id[0]
        else:
            return None

def oplan3_cenz_worker(program_id):
    with connections['oplan3'].cursor() as cursor:
        query_oplan3 = f'''
        SELECT [IntValue]
        FROM [oplan3].[dbo].[ProgramCustomFieldValues] 
        WHERE [ObjectId] = {program_id}
        AND [ProgramCustomFieldId] = 15
        '''
        cursor.execute(query_oplan3)
        oplan3_worker_id = cursor.fetchone()
        if oplan3_worker_id:
            return oplan3_worker_id[0]
        else:
            return None
