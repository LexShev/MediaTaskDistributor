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

def oplan_task_list(dates, program_type=(4, 5, 6, 10, 11, 12)):
    with connections['oplan3'].cursor() as cursor:
        channels_id = (2, 3, 4, 5, 6, 7, 8, 9, 10, 12)
        schedules_id = (3, 5, 6, 7, 8, 9, 10, 11, 12, 20)
        order = 'ASC'

        columns = [('Progs', 'program_id'), ('SchedDay', 'day_date'), ('Task', 'task_status')]
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
            LEFT JOIN [planner].[dbo].[task_list] AS Task
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
        print(query)
        cursor.execute(query)
        material_list_sql = cursor.fetchall()
        return material_list_sql, django_columns

def oplan_material_list(columns, dates, program_type=(4, 5, 6, 10, 11, 12)):
    with connections['oplan3'].cursor() as cursor:
        channels_id = (2, 3, 4, 5, 6, 7, 8, 9, 10, 12)
        schedules_id = (3, 5, 6, 7, 8, 9, 10, 11, 12, 20)
        order = 'ASC'

        # columns = [('Progs', 'program_id'), ('Progs', 'parent_id'), ('SchedDay', 'schedule_id'),
        #            ('Progs', 'program_type_id'), ('Progs', 'name'), ('Progs', 'production_year'),
        #            ('Progs', 'AnonsCaption'), ('Progs', 'episode_num'),
        #            ('Progs', 'duration'), ('Files', 'Name'), ('SchedDay', 'day_date'),
        #            ('Task', 'engineer_id'), ('Task', 'sched_id'), ('Task', 'sched_date'),
        #            ('Task', 'work_date'), ('Task', 'task_status'), ('Task', 'file_path')]
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
            LEFT JOIN [planner].[dbo].[task_list] AS Task
                ON Progs.[program_id] = Task.[program_id]
            WHERE Files.[Deleted] = 0
            AND Files.[PhysicallyDeleted] = 0
            AND Clips.[Deleted] = 0
            AND Progs.[deleted] = 0
            AND SchedProg.[Deleted] = 0
            AND SchedDay.[schedule_id] IN {schedules_id}
            AND SchedDay.[day_date] IN {dates}
            AND Progs.[program_type_id] IN {program_type}
            AND Progs.[program_id] > 0
            ORDER BY SchedProg.[DateTime] {order}
            """
        print(query)
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



def planner_material_list(schedules_id, engineer_id, material_type, work_dates, task_status):
    schedules_id = check_param(schedules_id)
    engineer_id = check_param(engineer_id)
    material_type = check_mat_type(material_type)
    task_status = check_param(task_status)

    if isinstance(work_dates, str):
        work_dates = date_generator(work_dates)

    with connections['planner'].cursor() as cursor:
        order = 'ASC'
        columns = [('Progs', 'program_id'), ('Progs', 'parent_id'), ('Progs', 'program_type_id'), ('Progs', 'name'),
                   ('Progs', 'production_year'), ('Progs', 'AnonsCaption'), ('Progs', 'episode_num'),
                   ('Progs', 'duration'), ('Adult', 'Name'), ('Task', 'engineer_id'), ('Task', 'sched_id'),
                   ('Sched', 'schedule_name'), ('Task', 'sched_date'), ('Task', 'work_date'), ('Task', 'task_status')]
        sql_columns = ', '.join([f'{col}.[{val}]' for col, val in columns])
        django_columns = [f'{col}_{val}' for col, val in columns]
        query = f'''
        SELECT {sql_columns}
        FROM [planner].[dbo].[task_list] AS Task
        JOIN [oplan3].[dbo].[program] AS Progs
            ON Task.[program_id] = Progs.[program_id]
        JOIN [oplan3].[dbo].[program_type] AS Types
            ON Progs.[program_type_id] = Types.[program_type_id]
        LEFT JOIN [oplan3].[dbo].[AdultType] AS Adult
            ON Progs.[AdultTypeID] = Adult.[AdultTypeID]
        JOIN [oplan3].[dbo].[schedule] AS Sched
            ON Task.[sched_id] = Sched.[schedule_id]
        WHERE Progs.[deleted] = 0
        AND Task.[sched_id] IN {schedules_id}
        AND Task.[engineer_id] IN {engineer_id}
        AND Progs.[program_type_id] IN {material_type}
        AND Task.[work_date] IN {work_dates}
        AND Task.[task_status] IN {task_status}
        ORDER BY Task.[sched_date] {order}
        '''
        cursor.execute(query)
        material_list_sql = cursor.fetchall()
        return material_list_sql, django_columns

def parent_name(program_id):
    with connections['oplan3'].cursor() as cursor:
        query = f'SELECT [name] FROM [oplan3].[dbo].[program] WHERE [program_id] = {program_id}'
        cursor.execute(query)
        for name in cursor.fetchone():
            return name

def planner_task_list(program_id):
    with connections['planner'].cursor() as cursor:
        query_planner = f'''
        SELECT engineer_id, engineer, work_date, task_status
        FROM [planner].[dbo].[task_list]
        WHERE [program_id] = {program_id}'''
        cursor.execute(query_planner)
        task_list = cursor.fetchone()
        if task_list:
            return task_list
        else:
            return None, None, None, None

def oplan3_engineer(program_id):
    with connections['oplan3'].cursor() as cursor:
        query_oplan3 = f'''
        SELECT [IntValue]
        FROM [oplan3].[dbo].[ProgramCustomFieldValues]
        WHERE [ObjectId] = {program_id}
        AND [ProgramCustomFieldId] = 15
        '''
        cursor.execute(query_oplan3)
        int_value = cursor.fetchone()
        if int_value:
            return int_value[0]


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

def parent_adult_name(program_id):
    with connections['oplan3'].cursor() as cursor:
        query = f'''
        SELECT Adult.[Name]
        FROM [oplan3].[dbo].[program] AS Progs
        LEFT JOIN [oplan3].[dbo].[AdultType] AS Adult
            ON Progs.[AdultTypeID] = Adult.[AdultTypeID]
        WHERE Progs.[program_id] = {program_id}
        '''
        cursor.execute(query)
        adult_name = cursor.fetchone()
        if adult_name:
            return adult_name[0]