from django.db import connections
from planner.settings import OPLAN_DB, PLANNER_DB


def get_engineer_id(worker_id):
    with connections[PLANNER_DB].cursor() as cursor:
        cursor.execute(f'SELECT [engineer_id] FROM [{PLANNER_DB}].[dbo].[engineers_list] WHERE [worker_id] = %s', (worker_id,))
        engineer_id = cursor.fetchone()
        if engineer_id:
            return engineer_id[0]
        else:
            return None