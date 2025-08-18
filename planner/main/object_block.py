from django.db import connections
from datetime import datetime
from planner.settings import OPLAN_DB, PLANNER_DB


def check_oplan3_lock(program_id):
    with connections[OPLAN_DB].cursor() as cursor:
        query = f'''
        SELECT [UserID], [LockTime]
        FROM [{OPLAN_DB}].[dbo].[ObjectLock]
        WHERE [ObjectID] = %s
        '''
        cursor.execute(query, (program_id,))
        lock = cursor.fetchone()
        if lock:
            return 'Oplan3', lock

def check_planner_lock(program_id):
    with connections[PLANNER_DB].cursor() as cursor:
        query = f'SELECT [worker_id], [lock_time] FROM [{PLANNER_DB}].[dbo].[material_lock] WHERE [program_id] = %s'
        cursor.execute(query, (program_id,))
        lock = cursor.fetchone()
        if lock:
            return 'Planner', lock

def block_object_planner(program_id, worker_id):
    with connections[PLANNER_DB].cursor() as cursor:
        query = f'''
        INSERT INTO [{PLANNER_DB}].[dbo].[material_lock]
        ([program_id], [worker_id], [lock_time])
        VALUES
        (%s, %s, %s);
        '''
        cursor.execute(query, (program_id, worker_id, datetime.now()))
        if cursor.rowcount:
            return  f'{program_id} was blocked'
        else:
            return 'skip'

def unblock_object_planner(program_id, worker_id):
    with connections[PLANNER_DB].cursor() as cursor:
        query = f'DELETE FROM [{PLANNER_DB}].[dbo].[material_lock] WHERE [program_id] = %s AND [worker_id] = %s'
        cursor.execute(query, (program_id, worker_id))
        if cursor.rowcount:
            return f'{program_id} was unblocked'
        else:
            return 'skip'