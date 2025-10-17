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

def task_info(field_dict, sql_set):
    with connections[PLANNER_DB].cursor() as cursor:
        columns = [
            ('Task', 'program_id'), ('Task', 'worker_id'), ('Task', 'duration'),
            ('Task', 'work_date'), ('Task', 'sched_date'), ('Task', 'sched_id'), ('Task', 'task_status'), ('Task', 'file_path'),
            ('Progs', 'program_type_id'), ('Progs', 'name'), ('Progs', 'orig_name'), ('Progs', 'keywords'),
            ('Progs', 'production_year'), ('Progs', 'episode_num')
        ]
        sql_columns = ', '.join([f'{col}.[{val}]' for col, val in columns])
        django_columns = [f'{col}_{val}' for col, val in columns]
        query = f'''
        SELECT DISTINCT TOP ({sql_set}) {sql_columns},
        (SELECT MIN([DateTime]) 
             FROM [{OPLAN_DB}].[dbo].[scheduled_program] 
             WHERE program_id = Progs.[program_id] 
                AND [Deleted] = 0
                AND [DateTime] >= CAST(GETDATE() AS DATE)
            ) as [DateTime]
        FROM [{PLANNER_DB}].[dbo].[task_list] AS Task
        JOIN [{OPLAN_DB}].[dbo].[program] AS Progs
            ON Task.[program_id] = Progs.[program_id]
        WHERE Progs.[deleted] = 0
        AND Progs.[DeletedIncludeParent] = 0
        {check_value('ready_date', field_dict.get('ready_date'))}
        {check_value('sched_date', field_dict.get('sched_date'))}
        {check_deadline(field_dict.get('deadline'))}
        {check_value('worker_id', field_dict.get('worker_id'))}
        {check_value('sched_id', field_dict.get('sched_id'))}
        {check_value('task_status', field_dict.get('task_status'))}
        {check_material_type(field_dict.get('material_type'))}
        ORDER BY Task.[work_date];
        '''
        cursor.execute(query)
        result = cursor.fetchall()
    material_list_sql = [dict(zip(django_columns, task)) for task in result]
    duration = []
    material_list = []
    program_id_list = []
    for material in material_list_sql:
        program_id = material.get('Task_program_id')
        if program_id in program_id_list:
            continue
        material['comments'] = comments_history(program_id, material.get('Progs_name'))
        duration.append(material.get('Task_duration'))
        if not material.get('Task_file_path'):
            material['Files_Name'] = find_file_path(program_id)
        if not material.get('Task_worker_id'):
            material['sender'] = ''
        program_id_list.append(program_id)
        material_list.append(material)
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
    return None


def update_comment(program_id, user_id, task_status=None, comment='Материал прошёл ОТК', deadline=None):
    try:
        with connections[PLANNER_DB].cursor() as cursor:
            values = (program_id, task_status, user_id, comment, deadline, datetime.today())
            query = f'''
                INSERT INTO [{PLANNER_DB}].[dbo].[comments_history]
                ([program_id], [task_status], [worker_id], [comment], [deadline], [time_of_change])
                VALUES (%s, %s, %s, %s, %s, %s);
                '''
            cursor.execute(query, values)
            if cursor.rowcount:
                return {'status': 'success', 'message': 'Изменения успешно внесены!'}
            else:
                return {'status': 'error', 'message': 'Изменения не внесены!'}
    except Exception as error:
        print(error)
        return {'status': 'error', 'message': str(error)}


def change_task_status(program_id, task_status, file_name, file_path):
    try:
        with connections[PLANNER_DB].cursor() as cursor:
            query = f'''
            UPDATE [{PLANNER_DB}].[dbo].[task_list]
            SET [task_status] = %s
            WHERE [program_id] = %s
            '''
            cursor.execute(query, (task_status, program_id))
            if cursor.rowcount:
                return {'status': 'success', 'message': f'Изменения для {file_name} успешно внесены!'}
            else:
                return {'status': 'error', 'message': 'Изменения не внесены!'}
    except Exception as error:
        print(error)
        return {'status': 'error', 'message': str(error)}


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
        columns = 'comment_id', 'worker_id', 'comment', 'deadline', 'time_of_change'
        sql_columns = ', '.join(columns)
        query = f'''
        SELECT {sql_columns}
        FROM [{PLANNER_DB}].[dbo].[comments_history]
        WHERE program_id = {program_id}
        AND [task_status] IN ('fix', 'final_fail')
        ORDER BY [time_of_change]
        '''
        cursor.execute(query)
        history = cursor.fetchall()
        comments_list = []
        for comment in history:
            comments_dict = {'Progs_name': progs_name}
            for key, val in zip(columns, comment):
                if key == 'time_of_change':
                    comments_dict[key] = val.strftime('%H:%M:%S %d-%m-%Y') or ''
                else:
                    comments_dict[key] = val
            comments_list.append(comments_dict)
        # json_data = json.dumps(res, default=json_serial, ensure_ascii=False, indent=2)
        return comments_list


def json_serial(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()