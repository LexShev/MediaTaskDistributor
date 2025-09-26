from datetime import datetime, timedelta

from django.db import connections

from planner.settings import PLANNER_DB, OPLAN_DB


def check_value(table, key, value):
    if value and len(value) == 1:
        return f"AND {table}.[{key}] = '{value[0]}'"
    elif value and len(value) > 1:
        return f"AND {table}.[{key}] IN {tuple(value)}"
    else:
        return ''

def check_sched(schedules):
    if not schedules:
        return ''
    if len(schedules) == 1:
        return f'AND (Sched.[schedule_id] = {schedules[0]} OR Task.program_id IS NOT NULL)'
    return f'AND (Sched.[schedule_id] IN {tuple(schedules)} OR Task.program_id IS NOT NULL)'

def check_material_type(material_type):
    if len(material_type) == 1:
        if 'season' in material_type:
            return 'AND Progs.[program_type_id] IN (4, 8, 12)'
        elif 'film' in material_type:
            return 'AND Progs.[program_type_id] IN (5, 6, 7, 10, 11, 16, 19)'
    return 'AND Progs.[program_type_id] IN (4, 5, 6, 7, 8, 10, 11, 12, 16, 19)'


def check_task_status(task_status):
    if not task_status:
        return ''
    if 'oplan_ready' not in task_status:
        if len(task_status) == 1:
            return f"AND Task.[task_status] = '{task_status[0]}'"
        else:
            return f"AND Task.[task_status] IN {tuple(task_status)}"
    else:
        return "AND Task.[task_status] IS NULL"



def check_dict(field_dict: dict) -> dict:
    for key, value in field_dict.items():
        if key in ('ready_dates', 'sched_dates'):
            field_dict[key] = [datetime.strptime(str_date, '%d.%m.%Y') for str_date in value.split(' - ')]
        elif key == 'schedules':
            if len(value) == 0:
                field_dict[key] = '(1, 3, 5, 6, 7, 8, 9, 10, 11, 12, 20, 99)'
            elif len(value) == 1:
                field_dict[key] = f'({value[0]})'
            else:
                field_dict[key] = tuple(value)
    return field_dict

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

def task_info(field_dict, sql_set):
    # field_dict = check_dict(field_dict)
    sched_date_start, sched_date_end = [datetime.strptime(str_date, '%d.%m.%Y') for str_date in field_dict.get('sched_dates').split(' - ')]
    sched_prog_end_date = sched_date_end + timedelta(days=1)
    # schedules = field_dict.get('schedules')


    with connections[PLANNER_DB].cursor() as cursor:
        columns = [
            ('Task', 'program_id'), ('Task', 'worker_id'), ('Progs', 'duration'),
            ('Task', 'work_date'), ('SchedDay', 'day_date'), ('Sched', 'schedule_id'), ('SchedProg', 'DateTime'), ('Task', 'task_status'), ('Task', 'file_path'),
            ('Progs', 'program_id'), ('Progs', 'program_type_id'), ('Progs', 'name'), ('Progs', 'orig_name'), ('Progs', 'keywords'),
            ('Progs', 'production_year'), ('Progs', 'episode_num')
        ]
        sql_columns = ', '.join([f'{col}.[{val}]' for col, val in columns])
        django_columns = [f'{col}_{val}' for col, val in columns]
        query = f'''
        SELECT DISTINCT TOP ({sql_set}) {sql_columns}
        FROM [{OPLAN_DB}].[dbo].[program] AS Progs
        JOIN [{OPLAN_DB}].[dbo].[scheduled_program] AS SchedProg
            ON Progs.[program_id] = SchedProg.[program_id]
        JOIN [{OPLAN_DB}].[dbo].[schedule_day] AS SchedDay
            ON SchedProg.[schedule_day_id] = SchedDay.[schedule_day_id]
        JOIN [{OPLAN_DB}].[dbo].[schedule] AS Sched
            ON SchedDay.[schedule_id] = Sched.[schedule_id]
        LEFT JOIN [{PLANNER_DB}].[dbo].[task_list] AS Task
            ON Progs.[program_id] = Task.[program_id]
        WHERE Progs.[deleted] = 0
        AND Progs.[DeletedIncludeParent] = 0
        AND SchedProg.[Deleted] = 0
        {check_value('Task', 'worker_id', field_dict.get('workers'))}
        {check_sched(field_dict.get('schedules'))}
        {check_task_status(field_dict.get('task_status'))}
        {check_material_type(field_dict.get('material_type'))}
        AND SchedProg.[DateTime] BETWEEN '{sched_date_start}' AND '{sched_prog_end_date}'
        AND Progs.[program_id] > 0
        ORDER BY SchedProg.[DateTime] ASC
        '''
        # AND SchedDay.[day_date] BETWEEN '{sched_dates[0]}' AND '{sched_dates[1]}'
        cursor.execute(query)
        result = cursor.fetchall()
    material_list = [dict(zip(django_columns, task)) for task in result]
    program_id_list = []
    for material in material_list:
        program_id = material.get('Progs_program_id')
        if program_id in program_id_list:
            material['is_duplicate'] = True
        if not material.get('Task_program_id') and not material.get('Task_worker_id'):
            material['Oplan_worker_id'] = oplan3_engineer(program_id)
            material['Oplan_status'] = 'oplan_ready'
        if not material.get('Task_file_path'):
            material['Files_Name'] = find_file_path(program_id)
        if not material.get('Task_worker_id'):
            material['sender'] = ''
        program_id_list.append(program_id)

    return material_list

def oplan3_engineer(program_id):
    try:
        with connections[OPLAN_DB].cursor() as cursor:
            query = f'''
            SELECT [worker_id]
            FROM [{PLANNER_DB}].[dbo].[engineers_list]
            WHERE [engineer_id] = (SELECT [IntValue]
                FROM [{OPLAN_DB}].[dbo].[ProgramCustomFieldValues] 
                WHERE [ObjectId] = {program_id}
                AND [ProgramCustomFieldId] = 15)
            '''
            cursor.execute(query)
            oplan_worker_id = cursor.fetchone()
            if oplan_worker_id:
                return oplan_worker_id[0]
    except Exception as error:
        print(error)
    return None