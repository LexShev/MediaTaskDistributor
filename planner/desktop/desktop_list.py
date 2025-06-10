from django.db import connections

from main.db_connection import parent_adult_name, check_mat_type

def prepare_exclusion_list(exclusion_list):
    if not exclusion_list:
        return ''
    if isinstance(exclusion_list, tuple) and len(exclusion_list) == 1:
        exclusion_list = exclusion_list[0], exclusion_list[0]
    return f'AND Task.[program_id] NOT IN {exclusion_list}'

def task_info(engineer_id, schedules, material_type, task_status, work_dates, exclusion_list):
    start_date, end_date = work_dates
    material_type = check_mat_type(material_type)

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
        AND Task.[engineer_id] = {engineer_id}
        AND Task.[sched_id] IN {tuple(schedules)}
        AND Progs.[program_type_id] IN {tuple(material_type)}
        AND Task.[work_date] BETWEEN '{start_date}' AND DATEADD(DAY, 21, '{end_date}')
        AND Task.[task_status] IN {tuple(task_status)}
        {prepare_exclusion_list(exclusion_list)}
        ORDER BY Progs.[name];
        '''
        cursor.execute(query)
        result = cursor.fetchall()
        material_list = [dict(zip(django_columns, task)) for task in result]
        for material_dict in material_list:
            if not material_dict.get('Adult_Name'):
                material_dict['Adult_Name'] = parent_adult_name(material_dict.get('Progs_parent_id'))
    return material_list

def cards_container(program_list):
    if not program_list:
        return []
    if isinstance(program_list, tuple) and len(program_list) == 1:
        program_list = program_list[0], program_list[0]
    columns = [
        ('Task', 'program_id'), ('Task', 'engineer_id'), ('Task', 'duration'), ('Task', 'work_date'),
        ('Task', 'sched_date'), ('Task', 'sched_id'), ('Task', 'task_status'), ('Task', 'file_path'),
        ('Progs', 'program_type_id'), ('Progs', 'name'), ('Progs', 'orig_name'), ('Progs', 'parent_id'),
        ('Progs', 'keywords'), ('Progs', 'production_year'), ('Progs', 'episode_num'), ('Adult', 'Name')
    ]
    sql_columns = ', '.join([f'{col}.[{val}]' for col, val in columns])
    django_columns = [f'{col}_{val}' for col, val in columns]
    with connections['planner'].cursor() as cursor:
        query = f'''
        SELECT {sql_columns}
        FROM [planner].[dbo].[task_list] AS Task
        JOIN [oplan3].[dbo].[program] AS Progs
            ON Task.[program_id] = Progs.[program_id]
        JOIN [planner].[dbo].[desktop_modelcardscontainer] AS Cont
            ON Task.[program_id] = Cont.[program_id]
        LEFT JOIN [oplan3].[dbo].[AdultType] AS Adult
            ON Progs.[AdultTypeID] = Adult.[AdultTypeID]
        WHERE Progs.[deleted] = 0
        AND Progs.[DeletedIncludeParent] = 0
        AND Task.[program_id] IN {program_list}
        ORDER BY Cont.[order];
        '''
        cursor.execute(query)
        result = cursor.fetchall()
        material_list = [dict(zip(django_columns, task)) for task in result]
        for material_dict in material_list:
            if not material_dict.get('Adult_Name'):
                material_dict['Adult_Name'] = parent_adult_name(material_dict.get('Progs_parent_id'))
    return material_list