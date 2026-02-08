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

def oplan_workers_dict():
    try:
        with connections[PLANNER_DB].cursor() as cursor:
            query = f'''
            SELECT [OplanUsers].[oplan_id], [first_name], [last_name]
            FROM [{PLANNER_DB}].[dbo].[auth_user] AS PlannerUsers
            JOIN [{PLANNER_DB}].[dbo].[oplan_users_list] AS OplanUsers
                ON [PlannerUsers].[id] = OplanUsers.[planner_id]
            '''
            cursor.execute(query)
            results = cursor.fetchall()
            return {worker[0]: f'{worker[1]} {worker[2]}' for worker in results}

    except Exception as error:
        print(error)
        return {}