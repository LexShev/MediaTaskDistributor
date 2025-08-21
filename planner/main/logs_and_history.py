from typing import Dict

from django.db import connections
from datetime import datetime, date

from main.js_requests import program_name
from main.helpers import get_engineer_id
from planner.settings import OPLAN_DB, PLANNER_DB



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
            with connections[PLANNER_DB].cursor() as cursor:
                query = f'''
                INSERT INTO [{PLANNER_DB}].[dbo].[history_list] ({sql_columns})
                VALUES ({program_id}, {old_field_id}, '', '', {worker_id}, GETDATE(), '{old_value}', '{new_value}');
                '''
                cursor.execute(query)

def insert_history_new(program_id, worker_id, old_values, new_values):
    columns = ('program_id', 'CustomFieldID', 'action_description', 'action_comment',
               'worker_id', 'time_of_change', 'old_value', 'new_value')
    sql_columns = ', '.join(columns)

    values_list = (
        (17, 'meta_form'),
        (7, 'work_date_form'),
        (14, 'cenz_rate_form'),
        (15, 'engineers_form'),
        (18, 'tags_form'),
        (19, 'inoagent_form'),
        (22, 'narc_select_form'),
        (8, 'lgbt_form'),
        (9, 'sig_form'),
        (10, 'obnazh_form'),
        (11, 'narc_form'),
        (12, 'mat_form'),
        (13, 'other_form'),
        (16, 'editor_form')
    )
    for num_key, name_key in values_list:
        old_value, new_value = old_values.get(num_key), new_values.get(name_key)
        old_value, new_value = check_data_type(old_value), check_data_type(new_value)
        if str(old_value) != str(new_value):
            with connections[PLANNER_DB].cursor() as cursor:
                query = f'''
                INSERT INTO [{PLANNER_DB}].[dbo].[history_list] ({sql_columns})
                VALUES ({program_id}, {num_key}, '', '', {worker_id}, GETDATE(), '{old_value}', '{new_value}');
                '''
                cursor.execute(query)

def select_actions(program_id):
    columns = ('program_id', 'CustomFieldID', 'action_description', 'action_comment',
               'worker_id', 'time_of_change', 'old_value', 'new_value')
    sql_columns = ', '.join(columns)
    with connections[PLANNER_DB].cursor() as cursor:
        query = f'''
        SELECT {sql_columns}
        FROM [{PLANNER_DB}].[dbo].[history_list]
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
    with connections[OPLAN_DB].cursor() as cursor:
        query = f'''
        SELECT {sql_columns}
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
        file_path_info = cursor.fetchone()
    if file_path_info:
        return dict(zip(django_columns, file_path_info))

def change_task_status(service_info_dict, task_status):
    program_id = service_info_dict.get('program_id')
    engineer_id = get_engineer_id(service_info_dict.get('worker_id'))
    work_date = service_info_dict.get('work_date')
    print('service_info_dict', engineer_id, work_date, task_status, program_id)

    with connections[PLANNER_DB].cursor() as cursor:
        select = f'SELECT [task_status] FROM [{PLANNER_DB}].[dbo].[task_list] WHERE [program_id] = {program_id}'
        cursor.execute(select)
        db_task_status = cursor.fetchone()
        if db_task_status and db_task_status[0]:
            if task_status == 'no_change':
                task_status = db_task_status[0]
            update_status = f'''
            UPDATE [{PLANNER_DB}].[dbo].[task_list]
            SET [engineer_id] = %s, [work_date] = %s, [ready_date] = GETDATE(), [task_status] = %s
            WHERE [program_id] = %s
            AND [task_status] IN ('ready', 'not_ready', 'fix_ready', 'otk_fail', 'no_material')
            '''
            cursor.execute(update_status, (engineer_id, work_date, task_status, program_id))
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
            INSERT INTO [{PLANNER_DB}].[dbo].[task_list] ({columns})
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            '''
            cursor.execute(query, values)
            return f'{program_name(program_id)} был добавлен в базу.'

def change_task_status_new(program_id, new_values, task_status, db_task_status) -> Dict[str, str]:
    engineer_id = new_values.get('engineers_form')
    work_date = new_values.get('work_date_form')
    program = program_name(program_id)
    with connections[PLANNER_DB].cursor() as cursor:
        if db_task_status:
            if task_status == 'fix':
                update_status = f'''
                    UPDATE [{PLANNER_DB}].[dbo].[task_list]
                    SET [task_status] = %s
                    WHERE [program_id] = %s
                    '''
                cursor.execute(update_status, (task_status, program_id))
                if cursor.rowcount:
                    return {'status': 'success', 'message': f'{program} завершено.'}
                else:
                    return {'status': 'error', 'message': f'Ошибка! Изменения не были внесены. {program}'}

            elif task_status == 'no_change':
                task_status = db_task_status
            update_status = f'''
                    UPDATE [{PLANNER_DB}].[dbo].[task_list]
                    SET [engineer_id] = %s, [work_date] = %s, [ready_date] = GETDATE(), [task_status] = %s
                    WHERE [program_id] = %s
                    '''
            cursor.execute(update_status, (engineer_id, work_date, task_status, program_id))
            if cursor.rowcount:
                return {'status': 'success', 'message': f'{program} завершено.'}
            else:
                return {'status': 'error', 'message': f'Ошибка! Изменения не были внесены. {program}'}

        else:
            file_path_dict = find_file_path(program_id)
            file_path = file_path_dict.get('Files_Name')
            duration = file_path_dict.get('Progs_duration')
            if not file_path:
                return {'status': 'error', 'message':  f'Ошибка! Изменения не были внесены. Медиафайл для {program} отсутствует.'}

            columns = '[program_id], [engineer_id], [duration], [work_date], [ready_date], [task_status], [file_path]'
            values = (program_id, engineer_id, duration, work_date, datetime.today(), task_status, file_path)
            query = f'''
                    INSERT INTO [{PLANNER_DB}].[dbo].[task_list] ({columns})
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    '''
            cursor.execute(query, values)
            return {'status': 'success', 'message': f'{program} был добавлен в базу.'}


def update_comment(program_id, worker_id, task_status=None, comment=None, deadline=None):
    with connections[PLANNER_DB].cursor() as cursor:
        values = (program_id, task_status, worker_id, comment, deadline, datetime.today())

        query = f'''
            INSERT INTO [{PLANNER_DB}].[dbo].[comments_history]
            ([program_id], [task_status], [worker_id], [comment], [deadline], [time_of_change])
            VALUES (%s, %s, %s, %s, %s, %s);
            '''
        cursor.execute(query, values)
    return 'Изменения успешно внесены!'

def get_task_status(program_id):
    with connections[PLANNER_DB].cursor() as cursor:
        cursor.execute(f'SELECT [task_status] FROM [{PLANNER_DB}].[dbo].[task_list] WHERE [program_id] = %s', (program_id,))
        res = cursor.fetchone()
        if res and res[0]:
            return res[0]
        return None