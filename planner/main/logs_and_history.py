from django.db import connections
from datetime import datetime, date

from main.js_requests import program_name


def check_data_type(value):
    if isinstance(value, datetime) or isinstance(value, date):
        return value.strftime('%Y-%m-%d')
    if value == None:
        return ''
    else:
        return str(value)

def insert_history(service_info_dict, old_values_dict, new_values_dict):
    program_id = service_info_dict.get('program_id')
    worker_id = service_info_dict.get('worker_id')

    columns = ('program_id', 'CustomFieldID', 'action_description', 'action_comment',
               'worker_id', 'time_of_change', 'old_value', 'new_value')
    sql_columns = ', '.join(columns)

    for old_field_id, new_field_id in zip(old_values_dict, new_values_dict):
        old_value, new_value = old_values_dict.get(old_field_id), new_values_dict.get(new_field_id)
        old_value, new_value = check_data_type(old_value), check_data_type(new_value)
        if str(old_value) != str(new_value):
            with connections['planner'].cursor() as cursor:
                query = f'''
                INSERT INTO [planner].[dbo].[history_list] ({sql_columns})
                VALUES ({program_id}, {old_field_id}, '', '', {worker_id}, GETDATE(), '{old_value}', '{new_value}');
                '''
                print(query)
                cursor.execute(query)

def select_actions(program_id):
    columns = ('program_id', 'CustomFieldID', 'action_description', 'action_comment',
               'worker_id', 'time_of_change', 'old_value', 'new_value')
    sql_columns = ', '.join(columns)
    with connections['planner'].cursor() as cursor:
        query = f'''
        SELECT {sql_columns}
        FROM [planner].[dbo].[history_list]
        WHERE [program_id] = {program_id}
        ORDER BY [time_of_change]
        '''
        cursor.execute(query)
        return [dict(zip(columns, actions)) for actions in cursor.fetchall()]

def find_file_path(program_id):
    columns = (('Files', 'Name'), ('Files', 'Size'), ('Files', 'CreationTime'),
               ('Files', 'ModificationTime'), ('Progs', 'duration'))
    sql_columns = ', '.join([f'{col}.[{val}]' for col, val in columns])
    django_columns = [f'{col}_{val}' for col, val in columns]
    with connections['oplan3'].cursor() as cursor:
        query = f'''
        SELECT {sql_columns}
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
        file_path_info = cursor.fetchone()
    if file_path_info:
        return dict(zip(django_columns, file_path_info))


def change_task_status(service_info_dict, task_status):
    program_id = service_info_dict.get('program_id')
    engineer_id = service_info_dict.get('engineer_id')
    work_date = service_info_dict.get('work_date')

    with connections['planner'].cursor() as cursor:
        select = f'SELECT [task_status] FROM [planner].[dbo].[task_list] WHERE [program_id] = {program_id}'
        cursor.execute(select)
        if cursor.fetchone():
            update_status = f'''
            UPDATE [planner].[dbo].[task_list]
            SET [task_status] = '{task_status}', [ready_date] = GETDATE()
            WHERE [program_id] = {program_id}
            AND [task_status] IN ('ready', 'not_ready', 'fix_ready', 'otk_fail', 'no_material')
            '''
            print('update_status', update_status)
            cursor.execute(update_status)
            if cursor.rowcount:
                return f'{program_name(program_id)} завершено.'

        else:
            file_path_dict = find_file_path(service_info_dict.get('program_id'))
            file_path = file_path_dict.get('Files_Name')
            duration = file_path_dict.get('Progs_duration')
            if not file_path:
                return f'Ошибка! Изменения не были внесены. Медиафайл для {program_name(program_id)} отсутствует.'

            columns = '[program_id], [engineer_id], [duration], [work_date], [ready_date], [task_status], [file_path]'
            values = (program_id, engineer_id, duration, work_date, datetime.today(), task_status, file_path)
            query = f'''
            INSERT INTO [planner].[dbo].[task_list] ({columns})
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            '''
            cursor.execute(query, values)
            return f'{program_name(program_id)} был добавлен в базу.'

def update_comment(program_id, worker_id, task_status=None, comment=None, deadline=None):
    with connections['planner'].cursor() as cursor:
        values = (program_id, task_status, worker_id, comment, deadline, datetime.today())

        query = f'''
            INSERT INTO [planner].[dbo].[comments_history]
            ([program_id], [task_status], [worker_id], [comment], [deadline], [time_of_change])
            VALUES (%s, %s, %s, %s, %s, %s);
            '''
        cursor.execute(query, values)
    return 'Изменения успешно внесены!'
