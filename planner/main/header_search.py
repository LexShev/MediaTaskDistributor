from django.db import connections
import datetime


def parent_adult_name(program_id):
    with connections['oplan3'].cursor() as cursor:
        query = f'''
        SELECT Progs.[program_id], Progs.[parent_id], Adult.[Name]
        FROM [oplan3].[dbo].[program] AS Progs
        LEFT JOIN [oplan3].[dbo].[AdultType] AS Adult
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

def calc_deadline(task_date):
    return task_date - datetime.timedelta(days=14)

def fast_search(program_name):
    with connections['planner'].cursor() as cursor:
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
        LEFT JOIN [oplan3].[dbo].[AdultType] AS Adult
            ON Progs.[AdultTypeID] = Adult.[AdultTypeID]
        JOIN [oplan3].[dbo].[schedule] AS Sched
            ON Task.[sched_id] = Sched.[schedule_id]
        WHERE Progs.[deleted] = 0
        AND Progs.[name] LIKE '%{program_name}%'
        ORDER BY Progs.[name];
        '''
        print(query)
        cursor.execute(query)
        result = cursor.fetchall()
    search_list = [dict(zip(django_columns, task)) for task in result]
    for temp_dict in search_list:
        if not temp_dict.get('Adult_Name'):
            temp_dict['Adult_Name'] = parent_adult_name(temp_dict.get('Progs_parent_id'))
        temp_dict['Task_deadline'] = calc_deadline(temp_dict['Task_sched_date'])
    return search_list

def advanced_search(search_id, search_query):
    columns_0 = [
        ('Progs', 'program_id'), ('Progs', 'parent_id'), ('Progs', 'program_type_id'), ('Progs', 'name'),
        ('Progs', 'production_year'), ('Progs', 'AnonsCaption'), ('Progs', 'episode_num'),
        ('Progs', 'duration'), ('Adult', 'Name')
    ]
    columns_1 = [
        ('Progs', 'program_id'), ('Progs', 'parent_id'), ('Progs', 'program_type_id'), ('Progs', 'name'),
        ('Progs', 'production_year'), ('Progs', 'AnonsCaption'), ('Progs', 'episode_num'),
        ('Progs', 'duration'), ('Adult', 'Name')
    ]
    columns_2 = [
        ('Progs', 'program_id'), ('Progs', 'parent_id'), ('Progs', 'program_type_id'), ('Progs', 'name'),
        ('Progs', 'production_year'), ('Progs', 'AnonsCaption'), ('Progs', 'episode_num'),
        ('Progs', 'duration'), ('Adult', 'Name'), ('Files', 'Name'), ('Files', 'Size'), ('Files', 'CreationTime'),
        ('Files', 'ModificationTime')
    ]
    columns_list = [columns_0, columns_1, columns_2]
    sql_columns = ', '.join([f'{col}.[{val}]' for col, val in columns_list[search_id]])
    django_columns = [f'{col}_{val}' for col, val in columns_list[search_id]]
    query_0 = f'''
        SELECT {sql_columns}
        FROM [oplan3].[dbo].[program] AS Progs
        LEFT JOIN [oplan3].[dbo].[AdultType] AS Adult
            ON Progs.[AdultTypeID] = Adult.[AdultTypeID]
        WHERE Progs.[deleted] = 0
        AND Progs.[program_id] = {search_query}
        ORDER BY Progs.[program_id];
        '''
    query_1 = f'''
        SELECT {sql_columns}
        FROM [oplan3].[dbo].[program] AS Progs
        LEFT JOIN [oplan3].[dbo].[AdultType] AS Adult
            ON Progs.[AdultTypeID] = Adult.[AdultTypeID]
        WHERE Progs.[deleted] = 0
        AND DeletedIncludeParent = 0
        AND [program_kind] IN (0, 3)
        AND Progs.[program_type_id] NOT IN (1, 2, 3, 9, 13, 14, 15)
        AND (Progs.[name] LIKE '%{search_query}%'
        OR Progs.[AnonsCaption] LIKE '%{search_query}%')
        ORDER BY Progs.[name];
        '''
    query_2 = f'''
        SELECT {sql_columns}
        FROM [oplan3].[dbo].[File] AS Files
        JOIN [oplan3].[dbo].[Clip] AS Clips
            ON Files.[ClipID] = Clips.[ClipID]
        JOIN [oplan3].[dbo].[program] AS Progs
            ON Clips.[MaterialID] = Progs.[SuitableMaterialForScheduleID]
        LEFT JOIN [oplan3].[dbo].[AdultType] AS Adult
            ON Progs.[AdultTypeID] = Adult.[AdultTypeID]
        JOIN [oplan3].[dbo].[program_type] AS Types
            ON Progs.[program_type_id] = Types.[program_type_id]
        WHERE Progs.[deleted] = 0
        AND Files.[Deleted] = 0
        AND Files.[PhysicallyDeleted] = 0
        AND Clips.[Deleted] = 0
        AND DeletedIncludeParent = 0
        AND [program_kind] IN (0, 3)
        AND Progs.[program_type_id] NOT IN (1, 2, 3, 9, 13, 14, 15)
        AND Files.[Name] LIKE '%{search_query}%'
        ORDER BY Files.[Name];
        '''
    query_list = [query_0, query_1, query_2]
    query = query_list[search_id]

    with connections['oplan3'].cursor() as cursor:
        print(query)
        cursor.execute(query)
        result = cursor.fetchall()
    search_list = [dict(zip(django_columns, task)) for task in result]
    for temp_dict in search_list:
        temp_dict['work_date'] = (cenz_info(temp_dict.get('Progs_program_id'))).get(7)
        temp_dict['engineer_id'] = (cenz_info(temp_dict.get('Progs_program_id'))).get(15)
        if not temp_dict.get('Adult_Name'):
            temp_dict['Adult_Name'] = parent_adult_name(temp_dict.get('Progs_parent_id'))
    print(search_list)
    return search_list

def cenz_info(program_id):
    with connections['oplan3'].cursor() as cursor:
        columns = '[ProgramCustomFieldId], [IntValue], [DateValue]'
        query = f'''
        SELECT {columns}
        FROM [oplan3].[dbo].[ProgramCustomFieldValues]
        WHERE [ObjectId] = {program_id}
        '''
        print(query)
        cursor.execute(query)
        cenz_info_sql = cursor.fetchall()
    custom_fields_dict = {}
    for cenz in cenz_info_sql:
        field_id, int_value, date_value = cenz
        # Дата отсмотра
        if field_id == 7:
            custom_fields_dict[field_id] = date_value
        elif field_id == 15:
            # custom_fields_dict[field_id] = items_string.split('\r\n')[int_value]
            custom_fields_dict[field_id] = int_value
            # .split(';')
    return custom_fields_dict
