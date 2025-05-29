from django.db import connections


def select_pool(sql_set):
    with connections['oplan3'].cursor() as cursor:
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
            FROM [oplan3].[dbo].[program] AS Progs
            WHERE Progs.[deleted] = 0
            AND Progs.[DeletedIncludeParent] = 0
            AND Progs.[SuitableMaterialForScheduleID] IS NOT NULL
            AND Progs.[program_type_id] IN (4, 5, 6, 10, 11, 12)
            AND Progs.[program_kind] IN (0, 3)
            AND Progs.[program_id] NOT IN
                (SELECT Task.[program_id] FROM [planner].[dbo].[task_list] AS Task)
            AND Progs.[program_id] NOT IN
                (SELECT [ObjectId] FROM [oplan3].[dbo].[ProgramCustomFieldValues]
                WHERE [ProgramCustomFieldId] = 15)
            '''
        print(query)
        cursor.execute(query)
        return [dict(zip(django_columns, material)) for material in cursor.fetchall()]

def get_total_count():
    with connections['oplan3'].cursor() as cursor:
        cursor.execute('''
            SELECT COUNT(Progs.[program_id]) AS total_count
            FROM [oplan3].[dbo].[program] AS Progs
            WHERE Progs.[deleted] = 0
            AND Progs.[DeletedIncludeParent] = 0
            AND Progs.[SuitableMaterialForScheduleID] IS NOT NULL
            AND Progs.[program_type_id] IN (4, 5, 6, 10, 11, 12)
            AND Progs.[program_kind] IN (0, 3)
            AND Progs.[program_id] NOT IN
                (SELECT Task.[program_id] FROM [planner].[dbo].[task_list] AS Task)
            AND Progs.[program_id] NOT IN
                (SELECT [ObjectId] FROM [oplan3].[dbo].[ProgramCustomFieldValues]
                WHERE [ProgramCustomFieldId] = 15)
        ''')
        total_count = cursor.fetchone()[0] or 0
    return {'total_count': total_count}

def get_film_stats():
    with connections['oplan3'].cursor() as cursor:
        cursor.execute('''
            SELECT COUNT(Progs.[program_id]) AS film_count, SUM(Progs.[duration]) AS film_dur
            FROM [oplan3].[dbo].[program] AS Progs
            WHERE Progs.[deleted] = 0
            AND Progs.[DeletedIncludeParent] = 0
            AND Progs.[SuitableMaterialForScheduleID] IS NOT NULL
            AND Progs.[program_type_id] IN (5, 6, 10, 11)
            AND Progs.[program_kind] IN (0, 3)
            AND Progs.[program_id] NOT IN
                (SELECT Task.[program_id] FROM [planner].[dbo].[task_list] AS Task)
            AND Progs.[program_id] NOT IN
                (SELECT [ObjectId] FROM [oplan3].[dbo].[ProgramCustomFieldValues]
                WHERE [ProgramCustomFieldId] = 15)
        ''')
        film_count, film_dur = cursor.fetchone() or (0, 0)
    return {'film_count': film_count, 'film_dur': film_dur}

def get_season_stats():
    with connections['oplan3'].cursor() as cursor:
        cursor.execute('''
            SELECT COUNT(Progs.[program_id]) AS season_count, SUM(Progs.[duration]) AS season_dur
            FROM [oplan3].[dbo].[program] AS Progs
            WHERE Progs.[deleted] = 0
            AND Progs.[DeletedIncludeParent] = 0
            AND Progs.[SuitableMaterialForScheduleID] IS NOT NULL
            AND Progs.[program_type_id] IN (4, 12)
            AND Progs.[program_kind] IN (0, 3)
            AND Progs.[program_id] NOT IN
                (SELECT Task.[program_id] FROM [planner].[dbo].[task_list] AS Task)
            AND Progs.[program_id] NOT IN
                (SELECT [ObjectId] FROM [oplan3].[dbo].[ProgramCustomFieldValues]
                WHERE [ProgramCustomFieldId] = 15)
        ''')
        season_count, season_dur = cursor.fetchone() or (0, 0)
    return {'season_count': season_count, 'season_dur': season_dur}

