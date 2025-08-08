from django.db import connections
from planner.settings import OPLAN_DB, PLANNER_DB


def home_common_table():
    columns = ('Task', 'program_id'), ('Progs', 'name'), ('Progs', 'production_year'), ('Task', 'duration'), ('Task', 'sched_date')
    sql_columns = ', '.join([f'{col}.[{val}]' for col, val in columns])
    django_columns = [f'{col}_{val}' for col, val in columns]
    query = f'''
    SELECT {sql_columns}
    FROM  [{PLANNER_DB}].[dbo].[task_list] AS Task
    LEFT JOIN [{OPLAN_DB}].[dbo].[program] AS Progs
        ON Task.[program_id] = Progs.[program_id]
    WHERE [sched_id] = 1
    AND Task.[task_status] = 'not_ready'
    ORDER BY Task.[sched_date], Progs.[name];
    '''
    with connections[OPLAN_DB].cursor() as cursor:
        cursor.execute(query)
        material_task_list = cursor.fetchall()
        if material_task_list:
            return [dict(zip(django_columns, material)) for material in material_task_list]
