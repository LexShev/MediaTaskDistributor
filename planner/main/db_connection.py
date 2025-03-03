from django.db import connections
import datetime


def oplan_material_list(program_type):
    with connections['oplan3'].cursor() as cursor:
        dates = ('2025-03-01', '2025-03-02', '2025-03-03', '2025-03-04', '2025-03-05', '2025-03-06', '2025-03-07', '2025-03-08', '2025-03-09', '2025-03-10', '2025-03-11', '2025-03-12', '2025-03-13', '2025-03-14', '2025-03-15', '2025-03-16', '2025-03-17', '2025-03-18', '2025-03-19', '2025-03-20', '2025-03-21', '2025-03-22', '2025-03-23', '2025-03-24', '2025-03-25', '2025-03-26', '2025-03-27', '2025-03-28', '2025-03-29')
        # dates = ('2025-03-01', '2025-03-02', '2025-03-03')

        channels = ('Кино +', 'Романтичный сериал', 'Крепкое', 'Советское родное кино')
        order = 'ASC'

        columns = [('Progs', 'program_id'), ('Progs', 'parent_id'), ('Progs', 'program_type_id'), ('Progs', 'name'),
                   ('Progs', 'production_year'), ('Progs', 'AnonsCaption'), ('Progs', 'episode_num'),
                   ('Progs', 'duration'), ('Sched', 'schedule_name'), ('SchedDay', 'day_date')]
        sql_columns = ', '.join([f'{col}.[{val}]' for col, val in columns])
        django_columns = [f'{col}_{val}' for col, val in columns]
        query = f'''
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
                    AND SchedDay.[day_date] IN {dates}
            JOIN [oplan3].[dbo].[schedule] AS Sched
                ON SchedDay.[schedule_id] = Sched.[schedule_id]
                    AND Sched.[schedule_name] IN {channels}
            WHERE Files.[Deleted] = 0
            AND Files.[PhysicallyDeleted] = 0
            AND Clips.[Deleted] = 0
            AND Progs.[deleted] = 0
            AND Progs.[program_type_id] IN {program_type}
            AND Progs.[program_id] > 0
            ORDER BY SchedProg.[DateTime] {order}
                    '''
        cursor.execute(query)
        material_list_sql = cursor.fetchall()
        return material_list_sql, django_columns

def planner_material_list(dates):
    with connections['planner'].cursor() as cursor:
        # dates = ('2025-03-01', '2025-03-02', '2025-03-03')

        channels = ('Кино +', 'Романтичный сериал', 'Крепкое', 'Советское родное кино')
        order = 'ASC'

        columns = [('Progs', 'program_id'), ('Progs', 'parent_id'), ('Progs', 'program_type_id'), ('Progs', 'name'),
                   ('Progs', 'production_year'), ('Progs', 'AnonsCaption'), ('Progs', 'episode_num'),
                   ('Progs', 'duration'), ('Sched', 'schedule_name'), ('SchedDay', 'day_date'),
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
                AND Sched.[schedule_name] IN {channels}
        WHERE Progs.[deleted] = 0
        AND Progs.[program_id] > 0
        AND Task.[work_date] IN {dates}
        ORDER BY SchedProg.[DateTime] {order}
        '''
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