from django.db import connections
from planner.settings import OPLAN_DB, PLANNER_DB


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


def program_name(program_id):
    with connections[OPLAN_DB].cursor() as cursor:
        query = f'SELECT [name] FROM [{OPLAN_DB}].[dbo].[program] WHERE [program_id] = %s'
        cursor.execute(query, (program_id,))
        name = cursor.fetchone()
        if name:
            return name[0]
        else:
            return program_id