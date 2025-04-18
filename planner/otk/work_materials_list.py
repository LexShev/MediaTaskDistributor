from django.db import connections


def task_info(work_dates):
    with connections['planner'].cursor() as cursor:
        columns = [
            ('Task', 'program_id'), ('Task', 'engineer_id'), ('Task', 'duration'),
            ('Task', 'work_date'), ('Task', 'sched_date'), ('Task', 'sched_id'), ('Task', 'task_status'), ('Task', 'file_path'),
            ('Progs', 'program_type_id'), ('Progs', 'name'), ('Progs', 'orig_name'), ('Progs', 'keywords'),
            ('Progs', 'production_year'), ('Progs', 'episode_num')
        ]
        sql_columns = ', '.join([f'{col}.[{val}]' for col, val in columns])
        django_columns = [f'{col}_{val}' for col, val in columns]
        query = f'''
        SELECT {sql_columns}
        FROM [planner].[dbo].[task_list] AS Task
        JOIN [oplan3].[dbo].[program] AS Progs
            ON Task.[program_id] = Progs.[program_id]
        WHERE Task.[work_date] = '{work_dates}'
        AND Task.[task_status] = 'ready'
        AND Progs.[deleted] = 0
        AND Progs.[DeletedIncludeParent] = 0
        ORDER BY Task.[work_date];
        '''
        print(query)
        cursor.execute(query)
        result = cursor.fetchall()
    return [dict(zip(django_columns, task)) for task in result]