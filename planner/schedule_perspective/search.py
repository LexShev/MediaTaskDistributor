from django.db import connections

from planner.settings import OPLAN_DB, PLANNER_DB


def fast_search(program_name) -> list:
    try:
        with connections[PLANNER_DB].cursor() as cursor:
            columns = [('Progs', 'program_id'), ('Progs', 'parent_id'), ('Progs', 'program_type_id'), ('Progs', 'name'),
                       ('Progs', 'production_year'), ('Progs', 'AnonsCaption'), ('Progs', 'episode_num'),
                       ('Progs', 'duration'), ('Adult', 'Name'), ('Task', 'worker_id'), ('Task', 'sched_id'),
                       ('Task', 'sched_date'), ('Task', 'work_date'), ('Task', 'task_status')]
            sql_columns = ', '.join([f'{col}.[{val}]' for col, val in columns])
            django_columns = [f'{col}_{val}' for col, val in columns]
            query = f'''
            SELECT TOP (7) {sql_columns}
            FROM [{PLANNER_DB}].[dbo].[task_list] AS Task
            JOIN [{OPLAN_DB}].[dbo].[program] AS Progs
                ON Task.[program_id] = Progs.[program_id]
            LEFT JOIN [{OPLAN_DB}].[dbo].[AdultType] AS Adult
                ON Progs.[AdultTypeID] = Adult.[AdultTypeID]
            WHERE Progs.[deleted] = 0
            AND Progs.[name] LIKE '%{program_name}%'
            ORDER BY Progs.[name];
            '''
            cursor.execute(query)
            result = cursor.fetchall()
        search_list = [dict(zip(django_columns, task)) for task in result]
        return search_list
    except Exception as error:
        print(error)
        return []