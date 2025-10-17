from typing import Dict

from django.db import connections
from datetime import datetime, date

from main.js_requests import program_name
from main.templatetags.custom_filters import status_name, engineer_id_to_worker_id
from planner.settings import OPLAN_DB, PLANNER_DB



def check_data_type(value):
    if isinstance(value, datetime) or isinstance(value, date):
        return value.strftime('%Y-%m-%d')
    if value is None:
        return ''
    else:
        return str(value)

def insert_history(service_info_dict, old_values_dict, new_values_dict):
    program_id = service_info_dict.get('program_id')
    user_id = service_info_dict.get('user_id')

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
                VALUES ({program_id}, {old_field_id}, '', '', {user_id}, GETDATE(), '{old_value}', '{new_value}');
                '''
                cursor.execute(query)

def insert_history_new(program_id, user_id, old_values, new_values):
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
                VALUES ({program_id}, {num_key}, '', '', {user_id}, GETDATE(), '{old_value}', '{new_value}');
                '''
                cursor.execute(query)

def insert_history_status(program_id, user_id, old_status, new_status):
    try:
        with connections[PLANNER_DB].cursor() as cursor:
            query = f'''
            INSERT INTO [{PLANNER_DB}].[dbo].[history_status_list]
            ([program_id], [worker_id], [time_of_change], [old_status], [new_status])
            VALUES (%s, %s, %s, %s, %s);
            '''
            cursor.execute(query, (program_id, user_id, datetime.today(), old_status, new_status))
    except Exception as error:
        print(error)

def select_actions(program_id):
    try:
        history_status = []
        with connections[PLANNER_DB].cursor() as cursor:
            history_list_columns = ('program_id', 'CustomFieldID', 'worker_id', 'time_of_change', 'old_value', 'new_value')
            sql_history_list_columns = ', '.join(history_list_columns)
            history_list_query = f'''
            SELECT {sql_history_list_columns}
            FROM [{PLANNER_DB}].[dbo].[history_list]
            WHERE [program_id] = %s
            ORDER BY [time_of_change]
            '''
            cursor.execute(history_list_query, (program_id,))
            history_status_result = cursor.fetchall()
            if history_status_result:
                history_status = [dict(zip(history_list_columns, actions)) for actions in history_status_result]

        history_status_list = []
        with connections[PLANNER_DB].cursor() as cursor:
            history_status_list_columns = ('program_id', 'worker_id', 'time_of_change', 'old_status', 'new_status')
            sql_history_status_list_columns = ', '.join(history_status_list_columns)
            history_status_list_query = f'''
            SELECT {sql_history_status_list_columns}
              FROM [{PLANNER_DB}].[dbo].[history_status_list]
              WHERE [program_id] = %s
            ORDER BY [time_of_change]
            '''
            cursor.execute(history_status_list_query, (program_id,))
            history_status_list_result = cursor.fetchall()
            if history_status_list_result:
                for actions in history_status_list_result:
                    temp_dict = dict(zip(history_status_list_columns, actions))
                    temp_dict['field_name'] = 'status'
                    history_status_list.append(temp_dict)
        return history_status + history_status_list
    except Exception as error:
        print(error)
        return []

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
    return {}

def change_task_status_new(program_id, new_values, task_status, db_task_status) -> Dict[str, str]:
    worker_id = engineer_id_to_worker_id(new_values.get('engineers_form'))
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
                    SET [worker_id] = %s, [work_date] = %s, [ready_date] = GETDATE(), [task_status] = %s
                    WHERE [program_id] = %s
                    '''
            cursor.execute(update_status, (worker_id, work_date, task_status, program_id))
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

            columns = '[program_id], [worker_id], [duration], [work_date], [ready_date], [task_status], [file_path]'
            values = (program_id, worker_id, duration, work_date, datetime.today(), task_status, file_path)
            query = f'''
                    INSERT INTO [{PLANNER_DB}].[dbo].[task_list] ({columns})
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    '''
            cursor.execute(query, values)
            return {'status': 'success', 'message': f'{program} был добавлен в базу.'}

def add_mark_no_cenz(program_id):
    try:
        with connections[PLANNER_DB].cursor() as cursor:
            query = f'''
                UPDATE [{PLANNER_DB}].[dbo].[task_list]
                SET [noCENZ] = 1
                WHERE [program_id] = %s
                '''
            cursor.execute(query, (program_id,))
            if cursor.rowcount:
                return {'status': 'success', 'message': 'mark noCENZ was added successfully'}
            else:
                return {'status': 'error', 'message': 'mark noCENZ was not added'}
    except Exception as error:
        print(error)
        return {'status': 'error', 'message': str(error)}

def update_comment(program_id, user_id, task_status=None, comment=None, deadline=None):
    try:
        with connections[PLANNER_DB].cursor() as cursor:
            values = (program_id, task_status, user_id, comment, deadline, datetime.today())

            query = f'''
                INSERT INTO [{PLANNER_DB}].[dbo].[comments_history]
                ([program_id], [task_status], [worker_id], [comment], [deadline], [time_of_change])
                VALUES (%s, %s, %s, %s, %s, %s);
                '''
            cursor.execute(query, values)
        return 'Изменения успешно внесены!'
    except Exception as error:
        print(error)
        return str(error)

def get_task_status(program_id):
    with connections[PLANNER_DB].cursor() as cursor:
        cursor.execute(f'SELECT [task_status] FROM [{PLANNER_DB}].[dbo].[task_list] WHERE [program_id] = %s', (program_id,))
        res = cursor.fetchone()
        if res and res[0]:
            return res[0]
        return None

def change_task_status_final(program_id, task_status, db_task_status):
    program = program_name(program_id)
    task_name = status_name(task_status)
    file_path_dict = find_file_path(program_id)
    file_path = file_path_dict.get('Files_Name')
    if not file_path:
        return {'status': 'error', 'message':  f'Ошибка! Изменения не были внесены. Медиафайл для {program} отсутствует.'}
    duration = file_path_dict.get('Progs_duration')
    with connections[PLANNER_DB].cursor() as cursor:
        if db_task_status:
            update_status = f'''
                UPDATE [{PLANNER_DB}].[dbo].[task_list]
                SET [duration] = %s, [task_status] = %s, [file_path] = %s
                WHERE [program_id] = %s
                '''
            cursor.execute(update_status, (duration, task_status, file_path, program_id))
            if cursor.rowcount:
                return {'status': 'success', 'message': f'{program} статус изменён на {task_name}.'}
            else:
                return {'status': 'error', 'message': f'Ошибка! Изменения не были внесены. {program}'}
        return {'status': 'error', 'message': f'Ошибка! Изменения не были внесены. {program} передача отсмотрена в Oplan.'}
        # else:
        #     oplan_info = cenz_info(program_id)
        #     columns = '[program_id], [worker_id], [duration], [work_date], [ready_date], [task_status], [file_path]'
        #     values = (program_id, oplan_info.get(15), duration, oplan_info.get(7), datetime.today(), task_status, file_path)
        #     query = f'''
        #             INSERT INTO [{PLANNER_DB}].[dbo].[task_list] ({columns})
        #             VALUES (%s, %s, %s, %s, %s, %s, %s)
        #             '''
        #     cursor.execute(query, values)
        #     return {'status': 'success', 'message': f'{program} был добавлен в базу.'}
