import datetime
from django.db import connections

def check_param(param):
    if len(param) == 1:
        return param[0], param[0],
    else:
        return tuple(param)

# def check_mat_type_obsolete(param):
#     if isinstance(param, str):
#         temp_list = [ast.literal_eval(mat) for mat in ast.literal_eval(param)]
#         param = []
#         for new in temp_list:
#             param.extend(new)
#         return tuple(param)
#     else:
#         return param

def check_mat_type(param):
    if param == ['film']:
        return 5, 6, 10, 11
    elif param == ['season']:
        return 4, 12
    else:
        return 4, 5, 6, 10, 11, 12


def oplan_material_list(program_type):
    with connections['oplan3'].cursor() as cursor:
        dates = tuple(str(datetime.date(day=1, month=3, year=2025)+datetime.timedelta(day)) for day in range(21))
        channels_id = (2, 3, 4, 5, 6, 7, 8, 9, 10, 12)

        order = 'ASC'

        columns = [('Progs', 'program_id'), ('Progs', 'parent_id'), ('Progs', 'program_type_id'), ('Progs', 'name'),
                   ('Progs', 'production_year'), ('Progs', 'AnonsCaption'), ('Progs', 'episode_num'),
                   ('Progs', 'duration'), ('Sched', 'schedule_id'), ('Sched', 'schedule_name'), ('SchedDay', 'day_date')]
        sql_columns = ', '.join([f'{col}.[{val}]' for col, val in columns])
        django_columns = [f'{col}_{val}' for col, val in columns]
        query = f"""
            SELECT {sql_columns}
            FROM [oplan3].[dbo].[File] AS Files
            JOIN [oplan3].[dbo].[Clip] AS Clips
                ON Files.[ClipID] = Clips.[ClipID]
            JOIN [oplan3].[dbo].[program] AS Progs
                ON Clips.[MaterialID] = Progs.[SuitableMaterialForScheduleID]
            JOIN [oplan3].[dbo].[program_type] AS Types
                ON Progs.[program_type_id] = Types.[program_type_id]
            JOIN [oplan3].[dbo].[scheduled_program] AS SchedProg
                ON Progs.[program_id] = SchedProg.[program_id]
            JOIN [oplan3].[dbo].[schedule_day] AS SchedDay
                ON SchedProg.[schedule_day_id] = SchedDay.[schedule_day_id]
            JOIN [oplan3].[dbo].[schedule] AS Sched
                ON SchedDay.[schedule_id] = Sched.[schedule_id]
            WHERE Files.[Deleted] = 0
            AND Files.[PhysicallyDeleted] = 0
            AND Clips.[Deleted] = 0
            AND Progs.[deleted] = 0
            AND Sched.[channel_id] IN {channels_id}
            AND SchedDay.[day_date] IN {dates}
            AND Progs.[program_type_id] IN {program_type}
            AND Progs.[program_id] > 0
            ORDER BY SchedProg.[DateTime] {order}
                    """
        print(query)
        cursor.execute(query)
        material_list_sql = cursor.fetchall()
        return material_list_sql, django_columns

def planner_material_list(channels, worker_id, material_type, work_dates, task_status):
    channels = check_param(channels)
    worker_id = check_param(worker_id)
    material_type = check_mat_type(material_type)
    task_status = check_param(task_status)

    if isinstance(work_dates, str):
        work_dates = (work_dates, work_dates)

    with connections['planner'].cursor() as cursor:
        order = 'ASC'
        columns = [('Progs', 'program_id'), ('Progs', 'parent_id'), ('Progs', 'program_type_id'), ('Progs', 'name'),
                   ('Progs', 'production_year'), ('Progs', 'AnonsCaption'), ('Progs', 'episode_num'),
                   ('Progs', 'duration'), ('Sched', 'schedule_id'), ('Sched', 'schedule_name'), ('SchedDay', 'day_date'),
                   ('Task', 'worker_id'), ('Task', 'worker'), ('Task', 'work_date'), ('Task', 'task_status')]
        sql_columns = ', '.join([f'{col}.[{val}]' for col, val in columns])
        django_columns = [f'{col}_{val}' for col, val in columns]
        query = f'''
        SELECT {sql_columns}
        FROM [planner].[dbo].[task_list] AS Task
        JOIN [oplan3].[dbo].[program] AS Progs
            ON Task.[program_id] = Progs.[program_id]
        JOIN [oplan3].[dbo].[program_type] AS Types
            ON Progs.[program_type_id] = Types.[program_type_id]
        JOIN [oplan3].[dbo].[scheduled_program] AS SchedProg
            ON Progs.[program_id] = SchedProg.[program_id]
        JOIN [oplan3].[dbo].[schedule_day] AS SchedDay
            ON SchedProg.[schedule_day_id] = SchedDay.[schedule_day_id]
        JOIN [oplan3].[dbo].[schedule] AS Sched
            ON SchedDay.[schedule_id] = Sched.[schedule_id]
        WHERE Progs.[deleted] = 0
        AND Sched.[channel_id] IN {channels}
        AND Task.[worker_id] IN {worker_id}
        AND Progs.[program_type_id] IN {material_type}
        AND Task.[work_date] IN {work_dates}
        AND Task.[task_status] IN {task_status}
        ORDER BY SchedProg.[DateTime] {order}
        '''
        # print(query)
        cursor.execute(query)
        material_list_sql = cursor.fetchall()

        return material_list_sql, django_columns

def planner_task_list(program_id):
    with connections['planner'].cursor() as cursor:
        query_planner = f'''
        SELECT worker_id, worker, work_date, task_status
        FROM [planner].[dbo].[task_list]
        WHERE [program_id] = {program_id}'''
        cursor.execute(query_planner)
        task_list = cursor.fetchone()
        if task_list:
            return task_list
        else:
            return None, None, None, None

def oplan3_cenz_worker(program_id):
    with connections['oplan3'].cursor() as cursor:
        columns = 'Val.[IntValue], Fields.[ItemsString]'
        query_oplan3 = f'''
        SELECT {columns}
        FROM [oplan3].[dbo].[ProgramCustomFields] AS Fields
        JOIN [oplan3].[dbo].[ProgramCustomFieldValues] AS Val
            ON Fields.[CustomFieldID] = Val.[ProgramCustomFieldId]
        WHERE Val.[ObjectId] = {program_id}
        AND Val.[ProgramCustomFieldId] = 15
        '''
        cursor.execute(query_oplan3)
        oplan3_worker_list = cursor.fetchone()
        if oplan3_worker_list:
            int_value, items_string = oplan3_worker_list
            return int_value, items_string.split('\r\n')[int_value]
        else:
            return None, None

def program_custom_fields():
    with connections['oplan3'].cursor() as cursor:
        query = f'''
        SELECT [CustomFieldID], [ItemsString]
        FROM [oplan3].[dbo].[ProgramCustomFields]
        WHERE [CustomFieldID] IN (15, 18, 19)
        '''
        cursor.execute(query)
        fields_list = cursor.fetchall()
        fields_dict = {}
        if fields_list:
            for field_id, items_string in fields_list:
                fields_dict[field_id] = items_string
        return fields_dict