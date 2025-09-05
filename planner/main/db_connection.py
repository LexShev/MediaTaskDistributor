import datetime
from django.db import connections
from planner.settings import OPLAN_DB, PLANNER_DB

def check_param(param):
    if len(param) == 1:
        return param[0], param[0],
    else:
        return tuple(param)

def check_mat_type(param):
    if param == ['film']:
        return 5, 6, 7, 10, 11, 19
    elif param == ['season']:
        return 4, 8, 12, 16, 20
    else:
        return 4, 5, 6, 7, 8, 10, 11, 12, 16, 19, 20

def oplan_task_list(dates, program_type=(4, 5, 6, 10, 11, 12)):
    with connections[OPLAN_DB].cursor() as cursor:
        channels_id = (2, 3, 4, 5, 6, 7, 8, 9, 10, 12)
        schedules_id = (3, 5, 6, 7, 8, 9, 10, 11, 12, 20)
        order = 'ASC'

        columns = [('Progs', 'program_id'), ('SchedDay', 'day_date'), ('Task', 'task_status')]
        sql_columns = ', '.join([f'{col}.[{val}]' for col, val in columns])
        django_columns = [f'{col}_{val}' for col, val in columns]
        query = f"""
            SELECT {sql_columns}
            FROM [{OPLAN_DB}].[dbo].[File] AS Files
            JOIN [{OPLAN_DB}].[dbo].[Clip] AS Clips
                ON Files.[ClipID] = Clips.[ClipID]
            JOIN [{OPLAN_DB}].[dbo].[program] AS Progs
                ON Clips.[MaterialID] = Progs.[SuitableMaterialForScheduleID]
            JOIN [{OPLAN_DB}].[dbo].[program_type] AS Types
                ON Progs.[program_type_id] = Types.[program_type_id]
            JOIN [{OPLAN_DB}].[dbo].[scheduled_program] AS SchedProg
                ON Progs.[program_id] = SchedProg.[program_id]
            JOIN [{OPLAN_DB}].[dbo].[schedule_day] AS SchedDay
                ON SchedProg.[schedule_day_id] = SchedDay.[schedule_day_id]
            JOIN [{OPLAN_DB}].[dbo].[schedule] AS Sched
                ON SchedDay.[schedule_id] = Sched.[schedule_id]
            LEFT JOIN [{PLANNER_DB}].[dbo].[task_list] AS Task
                ON Progs.[program_id] = Task.[program_id]
            WHERE Files.[Deleted] = 0
            AND Files.[PhysicallyDeleted] = 0
            AND Clips.[Deleted] = 0
            AND Progs.[deleted] = 0
            AND SchedDay.[schedule_id] IN {schedules_id}
            AND SchedDay.[day_date] IN {dates}
            AND Progs.[program_type_id] IN {program_type}
            AND Progs.[program_id] > 0
            ORDER BY SchedProg.[DateTime] {order}
            """
        cursor.execute(query)
        material_list_sql = cursor.fetchall()
        return material_list_sql, django_columns

def oplan_material_list(columns, dates, program_type=(4, 5, 6, 10, 11, 12)):
    with connections[OPLAN_DB].cursor() as cursor:
        channels_id = (2, 3, 4, 5, 6, 7, 8, 9, 10, 12)
        schedules_id = (3, 5, 6, 7, 8, 9, 10, 11, 12, 20)
        order = 'ASC'
        sql_columns = ', '.join([f'{col}.[{val}]' for col, val in columns])
        django_columns = [f'{col}_{val}' for col, val in columns]
        query = f"""
            SELECT {sql_columns}
            FROM [{OPLAN_DB}].[dbo].[File] AS Files
            JOIN [{OPLAN_DB}].[dbo].[Clip] AS Clips
                ON Files.[ClipID] = Clips.[ClipID]
            JOIN [{OPLAN_DB}].[dbo].[program] AS Progs
                ON Clips.[MaterialID] = Progs.[SuitableMaterialForScheduleID]
            JOIN [{OPLAN_DB}].[dbo].[program_type] AS Types
                ON Progs.[program_type_id] = Types.[program_type_id]
            JOIN [{OPLAN_DB}].[dbo].[scheduled_program] AS SchedProg
                ON Progs.[program_id] = SchedProg.[program_id]
            JOIN [{OPLAN_DB}].[dbo].[schedule_day] AS SchedDay
                ON SchedProg.[schedule_day_id] = SchedDay.[schedule_day_id]
            JOIN [{OPLAN_DB}].[dbo].[schedule] AS Sched
                ON SchedDay.[schedule_id] = Sched.[schedule_id]
            LEFT JOIN [{PLANNER_DB}].[dbo].[task_list] AS Task
                ON Progs.[program_id] = Task.[program_id]
            WHERE Files.[Deleted] = 0
            AND Files.[PhysicallyDeleted] = 0
            AND Clips.[Deleted] = 0
            AND Progs.[deleted] = 0
            AND Progs.[DeletedIncludeParent] = 0
            AND SchedProg.[Deleted] = 0
            AND SchedDay.[schedule_id] IN {schedules_id}
            AND SchedDay.[day_date] IN {dates}
            AND Progs.[program_type_id] IN {program_type}
            AND Progs.[program_id] > 0
            ORDER BY SchedProg.[DateTime] {order}
            """
        cursor.execute(query)
        material_list_sql = cursor.fetchall()
    return material_list_sql, django_columns

def date_generator(work_dates):
    start_date, end_date = work_dates.split(' - ')
    start_date = datetime.datetime.strptime(start_date, '%d/%m/%Y')
    end_date = datetime.datetime.strptime(end_date, '%d/%m/%Y')
    if start_date != end_date:
        delta = datetime.timedelta(days=1)
        dates_list = []
        while start_date <= end_date:
            dates_list.append(str(start_date.date()))
            start_date += delta
        return tuple(dates_list)
    else:
        return str(start_date.date()), str(start_date.date())

def date_splitter(work_dates):
    start_date, end_date = work_dates.split(' - ')
    start_date = datetime.datetime.strptime(start_date, '%d/%m/%Y')
    end_date = datetime.datetime.strptime(end_date, '%d/%m/%Y')
    return start_date, end_date

def get_order(user_order='sched_date', order_type='ASC'):
    order_dict = {
        'sched_date': 'Task.[sched_date]',
        'work_date': 'Task.[work_date]',
        'name': 'Progs.[name]',
        'duration': 'Progs.[duration]'
    }
    return f'{order_dict.get(user_order)} {order_type}'


def planner_material_list(schedules_id, engineer_id, material_type, work_dates, task_status, user_order, order_type):
    schedules_id = check_param(schedules_id)
    engineer_id = check_param(engineer_id)
    material_type = check_mat_type(material_type)
    task_status = check_param(task_status)
    start_date, end_date = work_dates

    with connections[PLANNER_DB].cursor() as cursor:
        columns = [('Progs', 'program_id'), ('Progs', 'parent_id'), ('Progs', 'program_type_id'), ('Progs', 'name'),
                   ('Progs', 'production_year'), ('Progs', 'AnonsCaption'), ('Progs', 'episode_num'),
                   ('Progs', 'duration'), ('Sched', 'schedule_id'), ('Adult', 'Name'), ('Task', 'engineer_id'), ('Task', 'sched_id'),
                   ('Task', 'sched_date'), ('Task', 'work_date'), ('Task', 'task_status')]
        sql_columns = ', '.join([f'{col}.[{val}]' for col, val in columns])
        django_columns = [f'{col}_{val}' for col, val in columns]
        query = f'''
        SELECT {sql_columns}
        FROM [{PLANNER_DB}].[dbo].[task_list] AS Task
        JOIN [{OPLAN_DB}].[dbo].[program] AS Progs
            ON Task.[program_id] = Progs.[program_id]
        JOIN [{OPLAN_DB}].[dbo].[program_type] AS Types
            ON Progs.[program_type_id] = Types.[program_type_id]
        LEFT JOIN [{OPLAN_DB}].[dbo].[AdultType] AS Adult
            ON Progs.[AdultTypeID] = Adult.[AdultTypeID]
        LEFT JOIN [{OPLAN_DB}].[dbo].[schedule] AS Sched
            ON Task.[sched_id] = Sched.[schedule_id]
        WHERE Progs.[deleted] = 0
        AND Task.[sched_id] IN {schedules_id}
        AND Task.[engineer_id] IN {engineer_id}
        AND Progs.[program_type_id] IN {material_type}
        AND Task.[work_date] BETWEEN '{start_date}' AND '{end_date}'
        AND Task.[task_status] IN {task_status}
        ORDER BY {get_order(user_order, order_type)}
        '''
        cursor.execute(query)
        material_list_sql = cursor.fetchall()
    return material_list_sql, django_columns

def parent_name(program_id):
    with connections[OPLAN_DB].cursor() as cursor:
        query = f'SELECT [name] FROM [{OPLAN_DB}].[dbo].[program] WHERE [program_id] = {program_id}'
        cursor.execute(query)
        for name in cursor.fetchone():
            return name

def planner_task_list(program_id):
    with connections[PLANNER_DB].cursor() as cursor:
        query_planner = f'''
        SELECT engineer_id, engineer, work_date, task_status
        FROM [{PLANNER_DB}].[dbo].[task_list]
        WHERE [program_id] = {program_id}'''
        cursor.execute(query_planner)
        task_list = cursor.fetchone()
        if task_list:
            return task_list
        else:
            return None, None, None, None

def oplan3_engineer(program_id):
    with connections[OPLAN_DB].cursor() as cursor:
        query_oplan3 = f'''
        SELECT [IntValue]
        FROM [{OPLAN_DB}].[dbo].[ProgramCustomFieldValues]
        WHERE [ObjectId] = {program_id}
        AND [ProgramCustomFieldId] = 15
        '''
        cursor.execute(query_oplan3)
        int_value = cursor.fetchone()
        if int_value:
            return int_value[0]


def program_custom_fields():
    with connections[OPLAN_DB].cursor() as cursor:
        query = f'''
        SELECT [CustomFieldID], [ItemsString]
        FROM [{OPLAN_DB}].[dbo].[ProgramCustomFields]
        WHERE [CustomFieldID] IN (15, 18, 19)
        '''
        cursor.execute(query)
        fields_list = cursor.fetchall()
        fields_dict = {}
        if fields_list:
            for field_id, items_string in fields_list:
                fields_dict[field_id] = items_string
        return fields_dict

def parent_adult_name(program_id):
    with connections[OPLAN_DB].cursor() as cursor:
        query = f'''
        SELECT Progs.[program_id], Progs.[parent_id], Adult.[Name]
        FROM [{OPLAN_DB}].[dbo].[program] AS Progs
        LEFT JOIN [{OPLAN_DB}].[dbo].[AdultType] AS Adult
            ON Progs.[AdultTypeID] = Adult.[AdultTypeID]
        WHERE Progs.[program_id] = {program_id}
        '''
        cursor.execute(query)
        adult_name = cursor.fetchone()
    if adult_name:
        if adult_name[2]:
            return adult_name[2]
        elif not adult_name[2] and adult_name[1]:
            return parent_adult_name(adult_name[1])
