from typing import Dict

from django.db import connections
from django.db import transaction
from datetime import datetime, date

from main.logs_and_history import get_task_status
from planner.settings import OPLAN_DB, PLANNER_DB

def check_value(key, value):
    if value is not None:
        return f"AND Task.[{key}] = '{value}'"
    else:
        return ''

def check_material_type(material_type):
    if material_type == 'season':
        return 'AND Progs.[program_type_id] IN (4, 8, 12, 16)'
    elif material_type == 'film':
        return 'AND Progs.[program_type_id] NOT IN (4, 8, 12, 16)'
    else:
        return ''

def check_deadline(value):
    if value:
        return f"AND Task.[sched_date] = DATEADD(DAY, -14, '{value}')"
    else:
        return ''

def choose_order(name):
    order_dict = {
        'progs_name': 'Progs.[name]',
        'engineers': 'Eng.[full_name]',
        'work_date': 'Task.[work_date]',
        'sched_date': 'Task.[sched_date]',
        'status': 'Task.[task_status]',
        'duration': 'Task.[duration]',
        'file_path': 'Task.[file_path]',
        'cenz': 'Task.[CENZ]',
    }
    return order_dict.get(name, 'Progs.[name]')

def check_extra_set(extra_set):
    if extra_set == 'deleted':
        return 'AND (Progs.[deleted] = 1 OR Progs.[DeletedIncludeParent] = 1)'
    elif extra_set == 'archived':
        return 'AND Task.[archived] = 1'
    elif extra_set == 'no_cenz':
        return 'AND Task.[CENZ] = 1'
    else:
        return ''

def search_condition(search_type, search_input):
    if not search_input:
        return ''
    if search_type == 0:
        try:
            return f"AND Task.[program_id] = {int(search_input)}"
        except (ValueError, TypeError):
            return ''
    elif search_type == 1:
        return f"AND Progs.[name] LIKE '%{search_input}%'"
    return ''


def task_info(field_dict, search_init_dict):
    sql_set = min(search_init_dict.sql_set or 5000, 5000)

    print(f"DEBUG task_info: field_dict={field_dict}, sql_set={sql_set}, type(field_dict)={type(field_dict)}")

    where_clauses = f'''
        Task.[program_id] IS NOT NULL
        {check_extra_set(field_dict.get('extra_set'))}
        {check_value('ready_date', field_dict.get('ready_date'))}
        {check_value('sched_date', field_dict.get('sched_date'))}
        {check_deadline(field_dict.get('deadline'))}
        {check_value('worker_id', field_dict.get('worker_id'))}
        {check_value('sched_id', field_dict.get('sched_id'))}
        {check_value('task_status', field_dict.get('task_status'))}
        {check_material_type(field_dict.get('material_type'))}
        {search_condition(search_init_dict.search_type, search_init_dict.search_input)}
        '''

    print(f"DEBUG task_info: where_clauses={where_clauses}")

    with connections[PLANNER_DB].cursor() as cursor:
        cursor.execute(f'''
        SELECT COUNT(Task.[program_id]), COALESCE(SUM(Task.[duration]), 0)
        FROM [{PLANNER_DB}].[dbo].[task_list] AS Task
        JOIN [{OPLAN_DB}].[dbo].[program] AS Progs
            ON Task.[program_id] = Progs.[program_id]
        JOIN [planner].dbo.[auth_user] AS Users
            ON Task.[worker_id] = Users.[id]
        WHERE {where_clauses}
        ''')
        total_count, total_duration = cursor.fetchone() or (0, 0)

        columns = [
            ('Task', 'program_id'), ('Task', 'worker_id'), ('Task', 'duration'), ('Task', 'work_date'),
            ('Task', 'sched_date'), ('Task', 'sched_id'), ('Task', 'task_status'), ('Task', 'file_path'),
            ('Task', 'archived'), ('Task', 'archiving_date'), ('Task', 'CENZ'), ('Users', 'first_name'), ('Users', 'last_name'),
            ('Progs', 'program_type_id'), ('Progs', 'name'), ('Progs', 'orig_name'), ('Progs', 'keywords'),
            ('Progs', 'production_year'), ('Progs', 'episode_num'), ('Progs', 'deleted'), ('Progs', 'DeletedIncludeParent')
        ]
        sql_columns = ', '.join([f'{col}.[{val}]' for col, val in columns])
        django_columns = [f'{col}_{val}' for col, val in columns]

        cursor.execute(f'''
        SELECT TOP ({sql_set}) {sql_columns}
        FROM [{PLANNER_DB}].[dbo].[task_list] AS Task
        JOIN [{OPLAN_DB}].[dbo].[program] AS Progs
            ON Task.[program_id] = Progs.[program_id]
        JOIN [planner].dbo.[auth_user] AS Users
            ON Task.[worker_id] = Users.[id]
        WHERE {where_clauses}
        ORDER BY {choose_order(search_init_dict.order)} {search_init_dict.order_type};
        ''')
        result = cursor.fetchall()

    task_list = [dict(zip(django_columns, task)) for task in result]

    program_id_list = [task.get('Task_program_id') for task in task_list if task.get('Task_program_id')]

    comments_by_program = comments_history(program_id_list)

    program_ids_without_file = [task.get('Task_program_id') for task in task_list
        if task.get('Task_program_id') and not task.get('Task_file_path')
    ]
    files_by_program = {}
    if program_ids_without_file:
        files_by_program = find_file_path(program_ids_without_file)

    for task in task_list:
        program_id = task.get('Task_program_id')
        task['comments'] = comments_by_program.get(program_id)
        if not task.get('Task_file_path'):
            task['Files_Name'] = files_by_program.get(program_id)
        if task.get('Progs_deleted') or task.get('Progs_DeletedIncludeParent'):
            task['is_deleted'] = True

    service_dict = {
        'total_duration': total_duration, 'total_count': total_count,
        'order': search_init_dict.order, 'order_type': search_init_dict.order_type
    }
    return task_list, service_dict


def process_update_task_list(user_id, program_id_check, program_id_list, engineers, work_dates, new_statuses, file_paths):
    try:
        if not program_id_check:
            return {'status': 'error', 'message': 'Не выбраны программы для обновления'}
        if not program_id_list or not engineers or not work_dates or not new_statuses:
            return {'status': 'error', 'message': 'Отсутствуют обязательные данные (инженер, дата или статус)'}

        if len(program_id_list) != len(engineers) or len(program_id_list) != len(work_dates) or len(program_id_list) != len(new_statuses):
            return {'status': 'error', 'message': 'Несоответствие количества данных в полях'}

        selector_data = [
            params for params in zip(program_id_list, engineers, work_dates, new_statuses, file_paths)
            if str(params[0]) in program_id_check
        ]
        if not selector_data:
            return {'status': 'error', 'message': 'Нет совпадающих данных для обновления'}

        with transaction.atomic(using=PLANNER_DB):
            with connections[PLANNER_DB].cursor() as cursor:
                for program_id, engineer, work_date, new_status, file_path in selector_data:
                    db_task_status = get_task_status(program_id)

                    cursor.execute(f'''
                    UPDATE [{PLANNER_DB}].[dbo].[task_list]
                    SET [worker_id] = %s, [work_date] = %s,
                        [task_status] = %s, [file_path] = %s
                    WHERE [program_id] = %s
                    ''', [engineer, work_date, new_status, file_path, program_id])

                    if db_task_status != new_status:
                        cursor.execute(f'''
                        INSERT INTO [{PLANNER_DB}].[dbo].[history_status_list]
                        ([program_id], [worker_id], [time_of_change], [old_status], [new_status])
                        VALUES (%s, %s, GETDATE(), %s, %s)
                        ''', [program_id, user_id, db_task_status, new_status])

                        cursor.execute(f'''
                        INSERT INTO [{PLANNER_DB}].[dbo].[comments_history]
                        ([program_id], [task_status], [worker_id], [comment], [time_of_change])
                        VALUES (%s, %s, %s, %s, GETDATE())
                        ''', [program_id, new_status, user_id, 'Статус задачи изменён администратором'])

                row_count = len(selector_data)

            return {
                'status': 'success',
                'message': f'Успешно обновлено записей: {row_count}',
                'count': row_count
            }
    except Exception as error:
        print(f"Error in process_update_task_list: {error}")
        return {'status': 'error', 'message': str(error)}

def process_reset_progress(user_id, program_id_check):
    try:
        if not program_id_check:
            return {'status': 'error', 'message': 'Пустой список для добавления'}

        with transaction.atomic(using=PLANNER_DB):
            with connections[PLANNER_DB].cursor() as cursor:
                history_values = [
                    (program_id, user_id, program_id, 'not_ready')
                    for program_id in program_id_check
                ]
                cursor.executemany(f'''
                INSERT INTO [{PLANNER_DB}].[dbo].[history_status_list]
                ([program_id], [worker_id], [time_of_change], [old_status], [new_status])
                VALUES (%s, %s, GETDATE(),
                    (SELECT task_status FROM [{PLANNER_DB}].[dbo].[task_list] WHERE program_id = %s),
                    %s)
                ''', history_values)

                comment_values = [
                    (program_id, 'not_ready', user_id, 'Статус задачи сброшен администратором')
                    for program_id in program_id_check
                ]
                cursor.executemany(f'''
                INSERT INTO [{PLANNER_DB}].[dbo].[comments_history]
                ([program_id], [task_status], [worker_id], [comment], [time_of_change])
                VALUES (%s, %s, %s, %s, GETDATE())
                ''', comment_values)

                reset_values = [
                    (program_id, user_id, program_id)
                    for program_id in program_id_check
                ]
                cursor.executemany(f'''
                UPDATE [{PLANNER_DB}].[dbo].[task_list]
                SET [task_status] = 'not_ready', [ready_date] = NULL, [CENZ] = NULL, [file_path] = (
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
                    AND Progs.[program_id] = %s
                )
                OUTPUT
                    INSERTED.program_id,
                    INSERTED.file_path,
                    INSERTED.task_status,
                    GETDATE(),
                    %s
                INTO [{PLANNER_DB}].[dbo].[filepath_history]
                    (program_id, file_path, task_status, time_of_change, worker_id)
                WHERE [program_id] = %s
                ''', reset_values)

                delete_values = [(program_id,) for program_id in program_id_check]
                cursor.executemany(f'''
                DELETE FROM [{OPLAN_DB}].[dbo].[ProgramCustomFieldValues]
                WHERE [ProgramCustomFieldId] IN (7, 14, 15)
                AND [ObjectId] = %s
                ''', delete_values)

            row_count = len(program_id_check)
            return {
                'status': 'success',
                'message': f'Успешно обновлено записей: {row_count}',
                'count': row_count
            }

    except Exception as error:
        print(f"Error in process_reset_progress: {error}")
        return {'status': 'error', 'message': str(error)}

def process_add_in_task_list(program_id_check, program_id_list, work_dates):
    try:
        if not program_id_check:
            return {'status': 'error', 'message': 'Пустой список для добавления'}
        if not program_id_list or not work_dates:
            return {'status': 'error', 'message': 'Отсутствуют необходимые данные'}

        selector_data = [
            (program_id, work_date)
            for program_id, work_date in zip(program_id_list, work_dates)
            if str(program_id) in program_id_check
        ]

        if not selector_data:
            return {'status': 'error', 'message': 'Массив данных содержит ошибку'}

        values_list = [(None, 99, work_date, None, program_id) for program_id, work_date in selector_data]
        with connections[PLANNER_DB].cursor() as cursor:
            query = f'''
            UPDATE [{PLANNER_DB}].[dbo].[task_list]
            SET [worker_id] = %s, [sched_id] = %s,
                [sched_date] = %s, [ready_date] = %s
            WHERE [program_id] = %s
            '''
            cursor.executemany(query, values_list)
            row_count = len(selector_data)
            connections[PLANNER_DB].commit()
            return {
                'status': 'success',
                'message': f'Успешно обновлено записей: {row_count}',
                'count': row_count
            }
    except Exception as error:
        print(f"Error in process_add_in_task_list: {error}")
        connections[PLANNER_DB].rollback()
        return {'status': 'error', 'message': str(error)}


def process_archive_task(program_id_check):
    try:
        if not program_id_check:
            return {'status': 'error', 'message': 'Пустой список для архивации'}

        program_id_list = [(program_id,) for program_id in program_id_check]

        with connections[PLANNER_DB].cursor() as cursor:
            query = f'''
            UPDATE [{PLANNER_DB}].[dbo].[task_list]
            SET [archived] = 1, [archiving_date] = GETDATE()
            WHERE [program_id] = %s
            '''
            cursor.executemany(query, program_id_list)
            row_count = len(program_id_check)
            connections[PLANNER_DB].commit()
            return {
                'status': 'success',
                'message': f'Успешно помещено в архив записей: {row_count}',
                'count': row_count
            }
    except Exception as error:
        print(error)
        connections[PLANNER_DB].rollback()
        return {'status': 'error', 'message': str(error)}


def process_del_task(program_id_check):
    try:
        if not program_id_check:
            return {'status': 'error', 'message': 'Пустой список для удаления'}

        program_id_list = [(program_id,) for program_id in program_id_check]
        with connections[PLANNER_DB].cursor() as cursor:
            query = f'''
            DELETE FROM [{PLANNER_DB}].[dbo].[task_list]
            WHERE [program_id] = %s
            '''
            cursor.executemany(query, program_id_list)
            row_count = len(program_id_check)
            connections[PLANNER_DB].commit()
            return {
                'status': 'success',
                'message': f'Успешно удалено записей: {row_count}',
                'count': row_count
            }
    except Exception as error:
        print(f"Error in process_del_task: {error}")
        connections[PLANNER_DB].rollback()
        return {'status': 'error', 'message': str(error)}


def find_file_path(program_id_list):
    if not program_id_list:
        return {}
    program_ids_str = ','.join(str(program_id) for program_id in program_id_list)
    with connections[OPLAN_DB].cursor() as cursor:
        query = f'''
        SELECT Progs.[program_id], Files.[Name]
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
        AND Progs.[program_id] IN ({program_ids_str})
        '''
        cursor.execute(query)
        results = cursor.fetchall()
    return {program_id: file_path for program_id, file_path in results}

def comments_history(program_id_list) -> dict:
    if not program_id_list:
        return {}
    program_ids_str = ','.join(str(program_id) for program_id in program_id_list)
    with connections[PLANNER_DB].cursor() as cursor:
        columns = 'program_id', 'comment_id', 'worker_id', 'first_name', 'last_name', 'comment', 'deadline', 'time_of_change'
        sql_columns = ', '.join(columns)
        query = f'''
        SELECT {sql_columns}
        FROM [{PLANNER_DB}].[dbo].[comments_history] AS Comments
        JOIN [planner].dbo.[auth_user] AS Users
            ON Comments.[worker_id] = Users.[id]
        WHERE program_id IN ({program_ids_str})
        AND [task_status] IN ('fix', 'fix_ready', 'final_fail') 
        ORDER BY [time_of_change]
        '''
        cursor.execute(query)
        history = cursor.fetchall()
        # comments_dict = [dict(zip(columns, task)) for task in history]

        comments_dict = {}
        for comment in history:
            program_id = comment[0]
            if program_id not in comments_dict:
                comments_dict[program_id] = []
            comments_dict[program_id].append(dict(zip(columns, comment)))
        return comments_dict