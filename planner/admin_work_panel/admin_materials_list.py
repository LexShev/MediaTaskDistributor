from typing import Dict

from django.db import connections
from datetime import datetime, date
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

def task_info(field_dict, search_init_dict):
    with connections[PLANNER_DB].cursor() as cursor:
        columns = [
            ('Task', 'program_id'), ('Task', 'worker_id'), ('Task', 'duration'), ('Task', 'work_date'),
            ('Task', 'sched_date'), ('Task', 'sched_id'), ('Task', 'task_status'), ('Task', 'file_path'),
            ('Task', 'archived'), ('Task', 'archiving_date'), ('Task', 'CENZ'),
            ('Progs', 'program_type_id'), ('Progs', 'name'), ('Progs', 'orig_name'), ('Progs', 'keywords'),
            ('Progs', 'production_year'), ('Progs', 'episode_num'), ('Progs', 'deleted'), ('Progs', 'DeletedIncludeParent')
        ]
        sql_columns = ', '.join([f'{col}.[{val}]' for col, val in columns])
        django_columns = [f'{col}_{val}' for col, val in columns]
        query = f'''
        SELECT TOP ({search_init_dict.sql_set}) {sql_columns}
        FROM [{PLANNER_DB}].[dbo].[task_list] AS Task
        JOIN [{OPLAN_DB}].[dbo].[program] AS Progs
            ON Task.[program_id] = Progs.[program_id]
        WHERE Task.[program_id] IS NOT NULL
        {check_extra_set(field_dict.get('extra_set'))}
        {check_value('ready_date', field_dict.get('ready_date'))}
        {check_value('sched_date', field_dict.get('sched_date'))}
        {check_deadline(field_dict.get('deadline'))}
        {check_value('worker_id', field_dict.get('worker_id'))}
        {check_value('sched_id', field_dict.get('sched_id'))}
        {check_value('task_status', field_dict.get('task_status'))}
        {check_material_type(field_dict.get('material_type'))}
        ORDER BY {choose_order(search_init_dict.order)} {search_init_dict.order_type};
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
        if material.get('Progs_deleted') or material.get('Progs_DeletedIncludeParent'):
            material['is_deleted'] = True
    total_duration = sum(duration)
    total_count = len(material_list)
    service_dict = {
        'total_duration': total_duration, 'total_count': total_count,
        'order': search_init_dict.order, 'order_type': search_init_dict.order_type
    }
    return material_list, service_dict


def update_task_list(request) -> Dict[str, str]:
    try:
        program_id_check = request.POST.getlist('program_id_check')
        program_id = request.POST.getlist('program_id')
        engineers = request.POST.getlist('workers_selector')
        work_date = request.POST.getlist('work_date_selector')
        status = request.POST.getlist('status_selector')
        file_path = request.POST.getlist('file_path')
        # Проверка на пустые данные
        if not program_id_check:
            return {'status': 'error', 'message': 'Не выбраны программы для обновления'}
        if not engineers or not work_date or not status:
            return {'status': 'error', 'message': 'Отсутствуют обязательные данные (инженер, дата или статус)'}

        # Проверка длины массивов
        if len(program_id) != len(engineers) or len(program_id) != len(work_date) or len(program_id) != len(status):
            return {'status': 'error', 'message': 'Несоответствие количества данных в полях'}
        # Фильтрация и подготовка данных
        selector_data = [
            params for params in zip(program_id, engineers, work_date, status, file_path)
            if params[0] in program_id_check
        ]
        if not selector_data:
            return {'status': 'error', 'message': 'Нет совпадающих данных для обновления'}
        # Подготовка данных для запроса с именованными параметрами
        values_list = [
            (engineer, work_date, status, file_path, program_id)
            for program_id, engineer, work_date, status, file_path in selector_data
        ]
        with connections[PLANNER_DB].cursor() as cursor:
            query = f'''
            UPDATE [{PLANNER_DB}].[dbo].[task_list]
            SET [worker_id] = %s, [work_date] = %s, 
                [task_status] = %s, [file_path] = %s
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
        print(f"Error in update_task_list: {error}")
        connections[PLANNER_DB].rollback()
        return {'status': 'error', 'message': str(error)}


from django.db import transaction


def reset_progress(request) -> Dict[str, str]:
    try:
        user_id = request.user.id
        program_id_check = request.POST.getlist('program_id_check')

        if not program_id_check:
            return {'status': 'error', 'message': 'Пустой список для добавления'}

        # Используем транзакцию Django
        with transaction.atomic(using=PLANNER_DB):
            with connections[PLANNER_DB].cursor() as cursor:
                # 1. Добавление в историю статусов
                history_values = [
                    (program_id, user_id, program_id, 'not_ready')
                    for program_id in program_id_check
                ]
                add_history = f'''
                INSERT INTO [{PLANNER_DB}].[dbo].[history_status_list]
                ([program_id], [worker_id], [time_of_change], [old_status], [new_status])
                VALUES (%s, %s, GETDATE(), 
                    (SELECT task_status FROM [{PLANNER_DB}].[dbo].[task_list] WHERE program_id = %s), 
                    %s)
                '''
                cursor.executemany(add_history, history_values)

                # 2. Добавление в историю комментариев
                comment_values = [
                    (program_id, 'not_ready', user_id, 'Статус задачи сброшен администратором')
                    for program_id in program_id_check
                ]
                add_comment = f'''
                INSERT INTO [{PLANNER_DB}].[dbo].[comments_history]
                ([program_id], [task_status], [worker_id], [comment], [time_of_change])
                VALUES (%s, %s, %s, %s, GETDATE())
                '''
                cursor.executemany(add_comment, comment_values)

                # 3. Сброс задачи + добавление в filepath_history
                reset_values = [
                    (program_id, user_id, program_id)
                    for program_id in program_id_check
                ]
                reset_task = f'''
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
                '''
                cursor.executemany(reset_task, reset_values)

                # 4. Удаление кастомных полей
                delete_values = [(program_id,) for program_id in program_id_check]
                cust_field_del = f'''
                DELETE FROM [{OPLAN_DB}].[dbo].[ProgramCustomFieldValues]
                WHERE [ProgramCustomFieldId] IN (7, 14, 15)
                AND [ObjectId] = %s
                '''
                cursor.executemany(cust_field_del, delete_values)

            row_count = len(program_id_check)
            # Автоматический коммит при успешном завершении блока with transaction.atomic
            return {
                'status': 'success',
                'message': f'Успешно обновлено записей: {row_count}',
                'count': row_count
            }

    except Exception as error:
        # Автоматический rollback при исключении
        print(f"Error in reset_progress: {error}")
        return {'status': 'error', 'message': str(error)}

def add_in_task_list(request) -> Dict[str, str]:
    try:
        program_id_check = request.POST.getlist('program_id_check')
        program_id = request.POST.getlist('program_id')
        work_date = request.POST.getlist('work_date_selector')

        # Проверка на пустые данные
        if not program_id_check:
            return {'status': 'error', 'message': 'Пустой список для добавления'}
        if not program_id or not work_date:
            return {'status': 'error', 'message': 'Отсутствуют необходимые данные'}

        # Фильтрация и подготовка данных
        selector_data = [params for params in zip(program_id, work_date) if params[0] in program_id_check]

        if not selector_data:
            return {'status': 'error', 'message': 'Массив данных содержит ошибку'}
        # Подготовка данных для запроса с именованными параметрами
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
        print(f"Error in add_in_task_list: {error}")
        connections[PLANNER_DB].rollback()
        return {'status': 'error', 'message': str(error)}


def archive_task(request) -> Dict[str, str]:
    try:
        program_id_check = request.POST.getlist('program_id_check')
        if not program_id_check:
            return {'status': 'error', 'message': 'Пустой список для архивации'}
        else:
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


def del_task(request) -> Dict[str, str]:
    try:
        program_id_check = request.POST.getlist('program_id_check')
        if not program_id_check:
            return {'status': 'error', 'message': 'Пустой список для удаления'}
        # Подготовка данных с именованными параметрами
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
        print(f"Error in del_task: {error}")
        connections[PLANNER_DB].rollback()
        return {'status': 'error', 'message': str(error)}


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

def comments_history(program_id, progs_name):
    with connections[PLANNER_DB].cursor() as cursor:
        columns = 'comment_id', 'worker_id', 'comment', 'deadline', 'time_of_change'
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