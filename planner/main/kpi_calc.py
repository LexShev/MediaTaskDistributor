from datetime import datetime, timedelta
from django.db import connections


work_date = datetime.now()

def kpi_worker(worker_id, date):
    with connections['planner'].cursor() as cursor:
        query = f'''SELECT SUM([duration])/8.0
        FROM [planner].[dbo].[task_list]
        WHERE [worker_id] = {worker_id}
        AND [datetime] = {date}
        AND [status] = 'ready'
        AND [vacation] = 0'''
        cursor.execute(query)
        kpi_w = cursor.fetchone()
    return kpi_w


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

def kpi_min(date):
    kpi_list = []
    with connections['planner'].cursor() as cursor:
        query_01 = f'''SELECT Worker.[worker_id], Worker.[worker]
                FROM [planner].[dbo].[worker_list] AS Worker
                WHERE '{date}' NOT IN (SELECT day_off FROM [planner].[dbo].[days_off])
                AND Worker.[fired] = 'False'
                '''
        cursor.execute(query_01)
        worker_list = cursor.fetchall()

        if worker_list:
            for worker_id, worker in worker_list:
                query_02 = f'''SELECT Task.[worker_id], Task.[worker], Task.[duration]
                FROM [planner].[dbo].[task_list] AS Task
                WHERE Task.[work_date] = '{date}'
                AND Task.[worker_id] = '{worker_id}'
                '''
                cursor.execute(query_02)
                kpi = sum([args[2] for args in cursor.fetchall()])/720000.0
                kpi_list.append((worker_id, worker, kpi))
    return sorted(kpi_list, key=lambda x: x[2])

def insert_film(program_id, worker_id, worker, duration, date, status):
    with connections['planner'].cursor() as cursor:
        columns = '[program_id], [worker_id], [worker], [duration], [work_date], [task_status]'
        query = f'''INSERT INTO [planner].[dbo].[task_list] ({columns})
        VALUES ({program_id}, {worker_id}, '{worker}', {duration}, '{date.strftime('%Y-%m-%d')}', '{status}')
        '''
        cursor.execute(query)
        print(f'{program_id}, {worker} successfully added')

def date_seek(date):
    kpi_info = kpi_min(date)
    if kpi_info and kpi_info[0][2] < 1:
        worker_id, worker, kpi = kpi_info[0]
        return worker_id, worker, kpi, date
    else:
        date += timedelta(days=1)
        return date_seek(date)

def distribution(program_id, program_type_id, duration):
    planner_worker_list, oplan3_worker_list = cenz_worker(program_id)
    if planner_worker_list:
        planner_worker_id, planner_worker = planner_worker_list
    else:
        planner_worker_id, planner_worker = None, None
    if oplan3_worker_list:
        int_value, items_string = oplan3_worker_list
        oplan3_worker_id = int_value
        oplan3_worker = items_string.split('\r\n')[int_value]
        print('oplan3_worker: ', oplan3_worker)
    else:
        oplan3_worker_id, oplan3_worker = None, None

    if program_type_id in (4, 5, 6, 10, 11, 12) and not oplan3_worker:
        date = datetime.now()
        if not planner_worker:
            status = 'not_ready'
            worker_id, worker, kpi, date = date_seek(date)
            insert_film(program_id, worker_id, worker, duration, date, status)
            print('\twork_date', date)
        else:
            worker_id = planner_worker_id
            worker = planner_worker
            status = 'not_ready'
    else:
        worker_id = oplan3_worker_id
        worker = oplan3_worker
        status = 'ready'
    return worker_id, worker, status, work_date

def cenz_worker(program_id):
    with connections['planner'].cursor() as cursor:
        query_planner = f'''SELECT worker_id, worker
        FROM [planner].[dbo].[task_list]
        WHERE [program_id] = {program_id}'''
        cursor.execute(query_planner)
        planner_worker_list = cursor.fetchone()
    with connections['oplan3'].cursor() as cursor:
        columns = 'Val.[IntValue], Fields.[ItemsString]'
        query_oplan3 = f'''
            SELECT {columns}
            FROM [oplan3].[dbo].[ProgramCustomFields] AS Fields
            JOIN [oplan3].[dbo].[ProgramCustomFieldValues] AS Val
                ON Fields.[CustomFieldID] = Val.[ProgramCustomFieldId]
            WHERE Val.[ObjectId] = {program_id}
            AND Val.[ProgramCustomFieldId] = 15
                '''
        cursor.execute(query_oplan3)
        oplan3_worker_list = cursor.fetchone()
    return planner_worker_list, oplan3_worker_list