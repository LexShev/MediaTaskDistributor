from django.db import connections
from datetime import datetime, date

from planner.settings import OPLAN_DB, PLANNER_DB

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

def task_info(field_dict, sql_set):
    with connections[PLANNER_DB].cursor() as cursor:
        columns = [
            ('Task', 'program_id'), ('Task', 'engineer_id'), ('Task', 'duration'),
            ('Task', 'work_date'), ('Task', 'sched_date'), ('Task', 'sched_id'), ('Task', 'task_status'), ('Task', 'file_path'),
            ('Progs', 'program_type_id'), ('Progs', 'name'), ('Progs', 'orig_name'), ('Progs', 'keywords'),
            ('Progs', 'production_year'), ('Progs', 'episode_num')
        ]
        sql_columns = ', '.join([f'{col}.[{val}]' for col, val in columns])
        django_columns = [f'{col}_{val}' for col, val in columns]
        query = f'''
        SELECT TOP ({sql_set}) {sql_columns}
        FROM [{PLANNER_DB}].[dbo].[task_list] AS Task
        JOIN [{OPLAN_DB}].[dbo].[program] AS Progs
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
        cursor.execute(query)
        result = cursor.fetchall()
    material_list = [dict(zip(django_columns, task)) for task in result]
    duration = []
    for material in material_list:
        material['comments'] = comments_history(material.get('Task_program_id'), material.get('Progs_name'))
        duration.append(material.get('Task_duration'))
        if not material.get('Task_file_path'):
            material['Files_Name'] = find_file_path(material.get('Task_program_id'))
    total_duration = sum(duration)
    total_count = len(material_list)
    service_dict = {'total_duration': total_duration, 'total_count': total_count}
    return material_list, service_dict

def find_file_path(program_id):
    with connections[OPLAN_DB].cursor() as cursor:
        query = f'''
        SELECT Files.[Name]
        FROM [{OPLAN_DB}].[dbo].[File] AS Files
        JOIN [{OPLAN_DB}].[dbo].[Clip] AS Clips
            ON Files.[ClipID] = Clips.[ClipID]
        JOIN [{OPLAN_DB}].[dbo].[program] AS Progs
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

# def change_task_status_batch(program_id_tuple, task_status):
#     with connections[PLANNER_DB].cursor() as cursor:
#         for program_id_list in program_id_tuple:
#             program_id = program_id_list.split(';')[0]
#             update = f'''
#             UPDATE [{PLANNER_DB}].[dbo].[task_list]
#             SET [task_status] = '{task_status}', [ready_date] = GETDATE()
#             WHERE [program_id] = {program_id}
#             '''
#             print(update)
#             cursor.execute(update)
#     return 'Изменения успешно внесены'

# def change_task_status_batch(program_list, task_status):
#     with connections[PLANNER_DB].cursor() as cursor:
#         for program in program_list:
#             program_id = program.get('program_id')
#             query = f'''
#             UPDATE [{PLANNER_DB}].[dbo].[task_list]
#             SET [task_status] = %s, [ready_date] = %s
#             WHERE [program_id] = %s'''
#             update_data = (task_status, datetime.today(), program_id)
#             print(query, update_data, 'without')
#             cursor.execute(query, update_data)
#     return 'Изменения успешно внесены'

#
# def update_comment_batch(program_id_tuple, task_status, worker_id, comment=None, deadline=None):
#     with connections[PLANNER_DB].cursor() as cursor:
#         for program_id_list in program_id_tuple:
#             program_id = program_id_list.split(';')[0]
#             values = (program_id, task_status, worker_id, comment, deadline, datetime.today())
#             query = f'''
#                 INSERT INTO [{PLANNER_DB}].[dbo].[comments_history]
#                 ([program_id], [task_status], [worker_id], [comment], [deadline], [time_of_change])
#                 VALUES (%s, %s, %s, %s, %s, %s);
#                 '''
#             cursor.execute(query, values)

def update_comment_batch(program_list, task_status, worker_id):
    with connections[PLANNER_DB].cursor() as cursor:
        for program in program_list:
            program_id = program.get('program_id')
            comment = program.get('comment')
            deadline = program.get('deadline')

            values = (program_id, task_status, worker_id, comment, deadline, datetime.today())
            query = f'''
                INSERT INTO [{PLANNER_DB}].[dbo].[comments_history]
                ([program_id], [task_status], [worker_id], [comment], [deadline], [time_of_change])
                VALUES (%s, %s, %s, %s, %s, %s);
                '''
            cursor.execute(query, values)

#
# def update_comment_otk_fail(otk_fail_tuple, task_status, worker_id, deadline=None):
#     with connections[PLANNER_DB].cursor() as cursor:
#         for material in otk_fail_tuple:
#             program_id, comment = material
#             values = (program_id, task_status, worker_id, comment, deadline, datetime.today())
#             query = f'''
#                  INSERT INTO [{PLANNER_DB}].[dbo].[comments_history]
#                  ([program_id], [task_status], [worker_id], [comment], [deadline], [time_of_change])
#                  VALUES (%s, %s, %s, %s, %s, %s);
#                  '''
#             print(query, values)
#             cursor.execute(query, values)

def change_task_status_batch(program_list, task_status):
    with connections[PLANNER_DB].cursor() as cursor:
        for program in program_list:
            program_id = program.get('program_id')
            file_path = program.get('file_path')
            if file_path:
                if file_path.startswith('"') and file_path.endswith('"'):
                    file_path = file_path[1:-1]
                query = f'''
                UPDATE [{PLANNER_DB}].[dbo].[task_list]
                SET [task_status] = %s, [ready_date] = %s, [file_path] = %s
                WHERE [program_id] = %s'''
                update_data = (task_status, datetime.today(), file_path, program_id)
                cursor.execute(query, update_data)
            else:
                query = f'''
                UPDATE [{PLANNER_DB}].[dbo].[task_list]
                SET [task_status] = %s, [ready_date] = %s
                WHERE [program_id] = %s'''
                update_data = (task_status, datetime.today(), program_id)
                cursor.execute(query, update_data)
    return 'Изменения успешно внесены'

def comments_history(program_id, progs_name):
    with connections[PLANNER_DB].cursor() as cursor:
        columns = 'worker_id', 'comment', 'deadline', 'time_of_change'
        sql_columns = ', '.join(columns)
        query = f'''
        SELECT {sql_columns}
        FROM [{PLANNER_DB}].[dbo].[comments_history]
        WHERE program_id = {program_id}
        AND [task_status] = 'fix'
        ORDER BY [time_of_change]
        '''
        cursor.execute(query)
        history = cursor.fetchall()
        comments_list = []
        for comment in history:
            comments_dict = {'Progs_name': progs_name}
            for key, val in zip(columns, comment):
                if key == 'deadline':
                    comments_dict[key] = val.strftime('%d-%m-%Y')
                elif key == 'time_of_change':
                    comments_dict[key] = val.strftime('%H:%M:%S %d-%m-%Y')
                else:
                    comments_dict[key] = val
            comments_list.append(comments_dict)
        # json_data = json.dumps(res, default=json_serial, ensure_ascii=False, indent=2)
        return comments_list


def json_serial(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()