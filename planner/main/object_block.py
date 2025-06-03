from django.db import connections
from datetime import datetime


def check_oplan3_lock(program_id):
    with connections['oplan3'].cursor() as cursor:
        query = f'SELECT [UserID], [LockTime] FROM [oplan3].[dbo].[ObjectLock] WHERE [ObjectID] = %s'
        cursor.execute(query, (program_id,))
        lock = cursor.fetchone()
        if lock:
            return 'Oplan3', lock

def check_planner_lock(program_id):
    with connections['planner'].cursor() as cursor:
        query = f'SELECT [worker_id], [lock_time] FROM [planner].[dbo].[material_lock] WHERE [program_id] = %s'
        cursor.execute(query, (program_id,))
        lock = cursor.fetchone()
        if lock:
            return 'Planner', lock

def block_object_planner(program_id, worker_id):
    with connections['planner'].cursor() as cursor:
        print('start')
        query = f'''
        INSERT INTO [planner].[dbo].[material_lock]
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
    with connections['planner'].cursor() as cursor:
        query = f'DELETE FROM [planner].[dbo].[material_lock] WHERE [program_id] = %s AND [worker_id] = %s'
        cursor.execute(query, (program_id, worker_id))
        if cursor.rowcount:
            return f'{program_id} was unblocked'
        else:
            return 'skip'