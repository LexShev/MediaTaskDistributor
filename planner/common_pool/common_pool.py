from django.db import connections
from planner.settings import OPLAN_DB, PLANNER_DB

def select_pool(sql_set):
    with connections[OPLAN_DB].cursor() as cursor:
        columns = [
            ('Progs', 'program_id'),
            ('Progs', 'parent_id'),
            ('Progs', 'program_type_id'),
            ('Progs', 'name'),
            ('Progs', 'production_year'),
            ('Progs', 'AnonsCaption'),
            ('Progs', 'episode_num'),
            ('Progs', 'duration')]
        sql_columns = ', '.join([f'{col}.[{val}]' for col, val in columns])
        django_columns = [f'{col}_{val}' for col, val in columns]
        query = f'''
            SELECT TOP ({sql_set}) {sql_columns}
            FROM [{OPLAN_DB}].[dbo].[program] AS Progs
            WHERE Progs.[deleted] = 0
            AND Progs.[DeletedIncludeParent] = 0
            AND Progs.[SuitableMaterialForScheduleID] IS NOT NULL
            AND Progs.[program_type_id] IN (4, 5, 6, 10, 11, 12)
            AND Progs.[program_kind] IN (0, 3)
            AND Progs.[program_id] NOT IN
                (SELECT Task.[program_id] FROM [{PLANNER_DB}].[dbo].[task_list] AS Task)
            AND Progs.[program_id] NOT IN
                (SELECT [ObjectId] FROM [{OPLAN_DB}].[dbo].[ProgramCustomFieldValues]
                WHERE [ProgramCustomFieldId] = 15)
            '''
        cursor.execute(query)
        return [dict(zip(django_columns, material)) for material in cursor.fetchall()]

def get_total_count():
    with connections[OPLAN_DB].cursor() as cursor:
        cursor.execute(f'''
            SELECT COUNT(Progs.[program_id]) AS total_count
            FROM [{OPLAN_DB}].[dbo].[program] AS Progs
            WHERE Progs.[deleted] = 0
            AND Progs.[DeletedIncludeParent] = 0
            AND Progs.[SuitableMaterialForScheduleID] IS NOT NULL
            AND Progs.[program_type_id] IN (4, 5, 6, 10, 11, 12)
            AND Progs.[program_kind] IN (0, 3)
            AND Progs.[program_id] NOT IN
                (SELECT Task.[program_id] FROM [{PLANNER_DB}].[dbo].[task_list] AS Task)
            AND Progs.[program_id] NOT IN
                (SELECT [ObjectId] FROM [{OPLAN_DB}].[dbo].[ProgramCustomFieldValues]
                WHERE [ProgramCustomFieldId] = 15)
        ''')
        total_count = cursor.fetchone()[0] or 0
    return {'total_count': total_count}

def get_film_stats():
    with connections[OPLAN_DB].cursor() as cursor:
        cursor.execute(f'''
            SELECT COUNT(Progs.[program_id]) AS film_count, SUM(Progs.[duration]) AS film_dur
            FROM [{OPLAN_DB}].[dbo].[program] AS Progs
            WHERE Progs.[deleted] = 0
            AND Progs.[DeletedIncludeParent] = 0
            AND Progs.[SuitableMaterialForScheduleID] IS NOT NULL
            AND Progs.[program_type_id] IN (5, 6, 10, 11)
            AND Progs.[program_kind] IN (0, 3)
            AND Progs.[program_id] NOT IN
                (SELECT Task.[program_id] FROM [{PLANNER_DB}].[dbo].[task_list] AS Task)
            AND Progs.[program_id] NOT IN
                (SELECT [ObjectId] FROM [{OPLAN_DB}].[dbo].[ProgramCustomFieldValues]
                WHERE [ProgramCustomFieldId] = 15)
        ''')
        film_count, film_dur = cursor.fetchone() or (0, 0)
    return {'film_count': film_count, 'film_dur': film_dur}

def get_season_stats():
    with connections[OPLAN_DB].cursor() as cursor:
        cursor.execute(f'''
            SELECT COUNT(Progs.[program_id]) AS season_count, SUM(Progs.[duration]) AS season_dur
            FROM [{OPLAN_DB}].[dbo].[program] AS Progs
            WHERE Progs.[deleted] = 0
            AND Progs.[DeletedIncludeParent] = 0
            AND Progs.[SuitableMaterialForScheduleID] IS NOT NULL
            AND Progs.[program_type_id] IN (4, 12)
            AND Progs.[program_kind] IN (0, 3)
            AND Progs.[program_id] NOT IN
                (SELECT Task.[program_id] FROM [{PLANNER_DB}].[dbo].[task_list] AS Task)
            AND Progs.[program_id] NOT IN
                (SELECT [ObjectId] FROM [{OPLAN_DB}].[dbo].[ProgramCustomFieldValues]
                WHERE [ProgramCustomFieldId] = 15)
        ''')
        season_count, season_dur = cursor.fetchone() or (0, 0)
    return {'season_count': season_count, 'season_dur': season_dur}

def insert_in_common_task(data):
    values = []
    program_id_list, sched_date = data
    for program_id in program_id_list:
        file_path, duration = find_file_path(program_id)
        task_status = 'not_ready'
        if not file_path:
            file_path = ''
            task_status = 'no_material'
        value = (program_id, duration, 1, sched_date, task_status, file_path)
        values.append(value)

    with connections[PLANNER_DB].cursor() as cursor:
        query = f'''
        INSERT INTO [{PLANNER_DB}].[dbo].[task_list] ([program_id], [duration], [sched_id], [sched_date], [task_status], [file_path])
        VALUES (%s, %s, %s, %s, %s, %s)
        '''
        cursor.executemany(query, values)
        cursor.execute("SELECT @@ROWCOUNT")
        return cursor.fetchone()[0]

def find_file_path(program_id):
    with connections[OPLAN_DB].cursor() as cursor:
        query = f'''
        SELECT Files.[Name], Progs.[duration]
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
        '''
        cursor.execute(query, (program_id,))
        res = cursor.fetchone()
        if res:
            file_path, duration = res
            return file_path, duration
        else:
            return None, None
