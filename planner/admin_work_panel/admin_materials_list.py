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
        ORDER BY Progs.[name];
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
    # print(material_list)
    return material_list, service_dict

def update_task_list(request):
    program_id_check = request.POST.getlist('program_id_check')
    program_id = request.POST.getlist('program_id')
    engineers = request.POST.getlist('engineers_selector')
    work_date = request.POST.getlist('work_date_selector')
    status = request.POST.getlist('status_selector')
    file_path = request.POST.getlist('file_path')
    if engineers and work_date and status:
        selector_data = [
            params for params in zip(program_id, engineers, work_date, status, file_path)
            if params[0] in program_id_check
        ]
        with connections[PLANNER_DB].cursor() as cursor:
            query = f'''
            UPDATE [{PLANNER_DB}].[dbo].[task_list]
            SET [engineer_id] = %s, [work_date] = %s, [task_status] = %s, [file_path] = %s
            WHERE [program_id] = %s
            '''
            values = [
                (engineer, work_date, status, file_path, program_id)
                for program_id, engineer, work_date, status, file_path in selector_data
            ]

            cursor.executemany(query, values)
            return cursor.rowcount

def add_in_common_task(request):
    program_id_check = request.POST.getlist('program_id_check')
    program_id = request.POST.getlist('program_id')
    work_date = request.POST.getlist('work_date_selector')
    if program_id and work_date:
        selector_data = [
            params for params in zip(program_id, work_date)
            if params[0] in program_id_check
        ]
        with connections[PLANNER_DB].cursor() as cursor:
            query = f'''
            UPDATE [{PLANNER_DB}].[dbo].[task_list]
            SET [engineer_id] = %s, [sched_id] = %s, [sched_date] = %s, [ready_date] = %s
            WHERE [program_id] = %s
            '''
            values = [(None, 1, work_date, None, program_id) for program_id, work_date in selector_data]
            cursor.executemany(query, values)
            return cursor.rowcount

def del_task(request):
    program_id_check = request.POST.getlist('program_id_check')
    if program_id_check:
        program_id_list = [(program_id,) for program_id in program_id_check]
        with connections[PLANNER_DB].cursor() as cursor:
            query = f'''
            DELETE FROM [{PLANNER_DB}].[dbo].[task_list]
            WHERE [program_id] IN (%s)
            '''
            cursor.executemany(query, program_id_list)
            return cursor.rowcount


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