from django.db import connections
from datetime import datetime

def check_value(key, value):
    if value:
        return f"AND Task.[{key}] = '{value}'"
    else:
        return ''

def check_material_type(material_type):
    if material_type == 'season':
        return 'AND Progs.[program_type_id] IN (4, 8, 12)'
    elif material_type == 'film':
        return 'AND Progs.[program_type_id] NOT IN (4, 8, 12)'
    else:
        return ''

def check_deadline(value):
    if value:
        return f"AND Task.[sched_date] = DATEADD(DAY, -14, '{value}')"
    else:
        return ''

def task_info(field_dict):
    # args = check_value(field_info)
    # fields = ('ready_date', 'sched_date', 'engineer_id', 'material_type', 'sched_id', 'task_status')
    # schedule_id = field_dict.get('schedule_id')
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
        WHERE Progs.[deleted] = 0
        AND Progs.[DeletedIncludeParent] = 0
        {check_value('ready_date', field_dict.get('ready_date'))}
        {check_value('sched_date', field_dict.get('sched_date'))}
        {check_deadline(field_dict.get('deadline'))}
        {check_value('engineer_id', field_dict.get('engineer_id'))}
        {check_value('sched_id', field_dict.get('sched_id'))}
        {check_value('task_status', field_dict.get('task_status'))}
        {check_material_type(field_dict.get('material_type'))}
        ORDER BY Task.[work_date];
        '''
        print(query)
        cursor.execute(query)
        result = cursor.fetchall()
    material_list = [dict(zip(django_columns, task)) for task in result]
    duration = []
    for material in material_list:
        duration.append(material.get('Task_duration'))
        if not material.get('Task_file_path'):
            material['Files_Name'] = find_file_path(material.get('Task_program_id'))
    total_duration = sum(duration)
    total_count = len(material_list)
    service_dict = {'total_duration': total_duration, 'total_count': total_count}
    return material_list, service_dict

def find_file_path(program_id):
    with connections['oplan3'].cursor() as cursor:
        query = f'''
        SELECT Files.[Name]
        FROM [oplan3].[dbo].[File] AS Files
        JOIN [oplan3].[dbo].[Clip] AS Clips
            ON Files.[ClipID] = Clips.[ClipID]
        JOIN [oplan3].[dbo].[program] AS Progs
            ON Clips.[MaterialID] = Progs.[SuitableMaterialForScheduleID]
        WHERE Files.[Deleted] = 0
        AND Files.[PhysicallyDeleted] = 0
        AND Clips.[Deleted] = 0
        AND Progs.[deleted] = 0
        AND Progs.[DeletedIncludeParent] = 0
        AND Progs.[program_id] = {program_id}
        '''
        cursor.execute(query)
        file_path = cursor.fetchone()
    if file_path:
        return file_path[0]

def change_task_status_batch(program_id_list, task_status):
    with connections['planner'].cursor() as cursor:
        for program_id in program_id_list:
            update = f'''
            UPDATE [planner].[dbo].[task_list]
            SET [task_status] = '{task_status}', [ready_date] = GETDATE()
            WHERE [program_id] = {program_id}'''
            cursor.execute(update)
            print(update)
    return 'Изменения успешно внесены'

def update_comment_batch(program_id_list, task_status, worker_id, comment, deadline):
    with connections['planner'].cursor() as cursor:
        for program_id in program_id_list:
            values = (program_id, task_status, worker_id, comment, deadline, datetime.today())
            query = f'''
                INSERT INTO [planner].[dbo].[comments_history]
                ([program_id], [task_status], [worker_id], [comment], [deadline], [time_of_change])
                VALUES (%s, %s, %s, %s, %s, %s);
                '''
            cursor.execute(query, values)

def change_task_status_fix(fix_tuple, task_status):
    with connections['planner'].cursor() as cursor:
        for material in fix_tuple:
            program_id, comment, file_path = material
            if file_path:
                if file_path.startswith('"') and file_path.endswith('"'):
                    file_path = file_path[1:-1]
                query = f'''
                UPDATE [planner].[dbo].[task_list]
                SET [task_status] = %s, [ready_date] = %s, [file_path] = %s
                WHERE [program_id] = %s'''
                update_data = (task_status, datetime.today(), file_path, program_id)
                print(query, update_data)
                cursor.execute(query, update_data)
            else:
                query = f'''
                UPDATE [planner].[dbo].[task_list]
                SET [task_status] = %s, [ready_date] = %s
                WHERE [program_id] = %s'''
                update_data = (task_status, datetime.today(), program_id)
                print(query, update_data)
                cursor.execute(query, update_data)
    return 'Изменения успешно внесены'

def update_comment_fix(fix_tuple, task_status, worker_id, deadline):
    with connections['planner'].cursor() as cursor:
        for material in fix_tuple:
            program_id, comment, file_path = material
            values = (program_id, task_status, worker_id, comment, deadline, datetime.today())
            query = f'''
                INSERT INTO [planner].[dbo].[comments_history]
                ([program_id], [task_status], [worker_id], [comment], [deadline], [time_of_change])
                VALUES (%s, %s, %s, %s, %s, %s);
                '''
            cursor.execute(query, values)