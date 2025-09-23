from django.db import connections

from planner.settings import PLANNER_DB, OPLAN_DB


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
    sched_dates = field_dict.get('sched_dates')
    schedules = field_dict.get('schedules')

    with connections[PLANNER_DB].cursor() as cursor:
        columns = [
            ('Task', 'program_id'), ('Task', 'worker_id'), ('Task', 'duration'),
            ('Task', 'work_date'), ('Task', 'sched_date'), ('Task', 'sched_id'), ('Task', 'task_status'), ('Task', 'file_path'),
            ('Progs', 'program_id'), ('Progs', 'program_type_id'), ('Progs', 'name'), ('Progs', 'orig_name'), ('Progs', 'keywords'),
            ('Progs', 'production_year'), ('Progs', 'episode_num')
        ]
        sql_columns = ', '.join([f'{col}.[{val}]' for col, val in columns])
        django_columns = [f'{col}_{val}' for col, val in columns]
        query = f'''
        SELECT TOP ({sql_set}) {sql_columns}
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
        AND SchedDay.[schedule_id] IN {schedules}
        AND SchedDay.[day_date] BETWEEN '{sched_dates[0]}' AND '{sched_dates[1]}'
        AND Progs.[program_id] > 0
        ORDER BY SchedProg.[DateTime] ASC

        '''
        # {check_value('ready_dates', field_dict.get('ready_dates'))}
        # {check_value('sched_dates', field_dict.get('sched_dates'))}
        # {check_value('workers', field_dict.get('workers'))}
        # {check_value('schedules', field_dict.get('schedules'))}
        # {check_value('task_status', field_dict.get('task_status'))}
        # {check_material_type(field_dict.get('material_type'))}
        cursor.execute(query)
        result = cursor.fetchall()
    material_list = [dict(zip(django_columns, task)) for task in result]
    duration = []
    for material in material_list:
        duration.append(material.get('Task_duration'))
        if not material.get('Task_file_path'):
            material['Files_Name'] = find_file_path(material.get('Progs_program_id'))
        if not material.get('Task_worker_id'):
            material['sender'] = ''
    # total_duration = sum(duration)
    # total_count = len(material_list)
    # service_dict = {'total_duration': total_duration, 'total_count': total_count}
    service_dict = {}
    return material_list, service_dict