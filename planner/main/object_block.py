from django.db import connections
from datetime import datetime
from planner.settings import OPLAN_DB, PLANNER_DB


def check_oplan3_lock(program_id):
    try:
        with connections[OPLAN_DB].cursor() as cursor:
            query = f'''
            SELECT Us.[user_name], Obj.[LockTime]
            FROM [{OPLAN_DB}].[dbo].[ObjectLock] AS Obj
            JOIN [{OPLAN_DB}].[dbo].[user] AS Us
                ON Obj.[UserID] = Us.[user_id]
            WHERE Obj.[ObjectID] = %s
            '''
            cursor.execute(query, (program_id,))
            lock = cursor.fetchone()
            if lock and len(lock) == 2:
                worker_name, lock_time = lock
                return {'status': 'success', 'message': 'locked', 'app': 'Oplan3',
                        'worker_name': worker_name, 'lock_time': lock_time}
            else:
                return {'status': 'success', 'message': 'not_locked'}
    except Exception as error:
        return {'status': 'error', 'message': str(error)}

def check_planner_lock(program_id, worker_id):
    try:
        with connections[PLANNER_DB].cursor() as cursor:
            query = f'''SELECT Us.[first_name], Us.[last_name], Mat.[lock_time]
            FROM [{PLANNER_DB}].[dbo].[material_lock] AS Mat
            JOIN [{PLANNER_DB}].[dbo].[auth_user] AS Us
                ON Mat.[worker_id] = Us.[id]
            WHERE Mat.[program_id] = %s
            AND Mat.[worker_id] != %s
            '''
            cursor.execute(query, (program_id, worker_id))
            lock = cursor.fetchone()
            if lock and len(lock) == 3:
                first_name, last_name, lock_time = lock
                return {'status': 'success', 'message': 'locked', 'app': 'Planner',
                 'worker_name': f'{first_name} {last_name}', 'lock_time': lock_time}
            else:
                return {'status': 'success', 'message': 'not_locked'}
    except Exception as error:
        return {'status': 'error', 'message': str(error)}

def block_object_planner(program_id, worker_id):
    try:
        with connections[PLANNER_DB].cursor() as cursor:
            query = f'''
            INSERT INTO [{PLANNER_DB}].[dbo].[material_lock]
            ([program_id], [worker_id], [lock_time])
            VALUES
            (%s, %s, %s);
            '''
            cursor.execute(query, (program_id, worker_id, datetime.now()))
            if cursor.rowcount:
                return  {'status': 'success', 'message': f'{program_id} was blocked'}
            else:
                return {'status': 'error', 'message': 'not_blocked'}
    except Exception as error:
        print(error)
        return {'status': 'error', 'message': error}

def unblock_object_planner(program_id, worker_id):
    with connections[PLANNER_DB].cursor() as cursor:
        query = f'DELETE FROM [{PLANNER_DB}].[dbo].[material_lock] WHERE [program_id] = %s AND [worker_id] = %s'
        cursor.execute(query, (program_id, worker_id))
        if cursor.rowcount:
            return f'{program_id} was unblocked'
        else:
            return 'skip'