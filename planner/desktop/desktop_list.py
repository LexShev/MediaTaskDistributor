from django.db import connections

from main.db_connection import parent_adult_name


def task_info(engineer_id, start_date, end_date):
    with connections['planner'].cursor() as cursor:
        columns = [
            ('Task', 'program_id'), ('Task', 'engineer_id'), ('Task', 'duration'), ('Task', 'work_date'),
            ('Task', 'sched_date'), ('Task', 'sched_id'), ('Task', 'task_status'), ('Task', 'file_path'),
            ('Progs', 'program_type_id'), ('Progs', 'name'), ('Progs', 'orig_name'), ('Progs', 'parent_id'),
            ('Progs', 'keywords'), ('Progs', 'production_year'), ('Progs', 'episode_num'), ('Adult', 'Name')
        ]
        sql_columns = ', '.join([f'{col}.[{val}]' for col, val in columns])
        django_columns = [f'{col}_{val}' for col, val in columns]
        query = f'''
        SELECT {sql_columns}
        FROM [planner].[dbo].[task_list] AS Task
        JOIN [oplan3].[dbo].[program] AS Progs
            ON Task.[program_id] = Progs.[program_id]
        LEFT JOIN [oplan3].[dbo].[AdultType] AS Adult
            ON Progs.[AdultTypeID] = Adult.[AdultTypeID]
        WHERE Progs.[deleted] = 0
        AND Progs.[DeletedIncludeParent] = 0
        AND Task.[engineer_id] = '{engineer_id}'
        AND Task.[work_date] BETWEEN '{start_date}' AND DATEADD(DAY, 21, '{end_date}')

        ORDER BY Task.[work_date];
        '''

        # {check_value('ready_date', field_dict.get('ready_date'))}
        # {check_value('sched_date', field_dict.get('sched_date'))}
        # {check_deadline(field_dict.get('deadline'))}
        # {check_value('engineer_id', field_dict.get('engineer_id'))}
        # {check_value('sched_id', field_dict.get('sched_id'))}
        # {check_value('task_status', field_dict.get('task_status'))}
        # {check_material_type(field_dict.get('material_type'))}

        print(query)
        cursor.execute(query)
        result = cursor.fetchall()
        material_list = [dict(zip(django_columns, task)) for task in result]
        for material_dict in material_list:
            if not material_dict.get('Adult_Name'):
                material_dict['Adult_Name'] = parent_adult_name(material_dict.get('Progs_parent_id'))
    return material_list