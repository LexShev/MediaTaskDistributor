from django.db import connections


def query_selector(search_id, sql_set, search_query):
    if not search_query:
        return []
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
    columns_3 = [
        ('Progs', 'program_id'), ('Progs', 'parent_id'), ('Progs', 'program_type_id'),
        ('Progs', 'name'), ('Progs', 'production_year'), ('Progs', 'AnonsCaption'), ('Progs', 'episode_num'),
        ('Progs', 'duration'), ('Task', 'engineer_id'), ('Task', 'sched_id'), ('Task', 'sched_date'),
        ('Task', 'work_date'), ('Task', 'task_status'), ('Task', 'file_path'), ('Adult', 'Name')
    ]
    columns_4 = [
        ('Progs', 'program_id'), ('Progs', 'parent_id'), ('SchedDay', 'schedule_id'), ('Progs', 'program_type_id'),
        ('Progs', 'name'), ('Progs', 'production_year'), ('Progs', 'AnonsCaption'), ('Progs', 'episode_num'),
        ('Progs', 'duration'), ('Files', 'Name'), ('Files', 'Size'), ('Files', 'ModificationTime'),
        ('SchedDay', 'day_date'), ('Task', 'engineer_id'), ('Task', 'sched_id'), ('Task', 'sched_date'),
        ('Task', 'work_date'), ('Task', 'task_status'), ('Task', 'file_path'), ('Adult', 'Name')
    ]
    columns_5 = [
        ('Progs', 'program_id'), ('Progs', 'parent_id'), ('SchedDay', 'schedule_id'), ('Progs', 'program_type_id'),
        ('Progs', 'name'), ('Progs', 'production_year'), ('Progs', 'AnonsCaption'), ('Progs', 'episode_num'),
        ('Progs', 'duration'), ('Files', 'Name'), ('Files', 'Size'), ('Files', 'ModificationTime'),
        ('SchedDay', 'day_date'), ('Task', 'engineer_id'), ('Task', 'sched_id'), ('Task', 'sched_date'),
        ('Task', 'work_date'), ('Task', 'task_status'), ('Task', 'file_path'), ('Adult', 'Name')
    ]

    columns_list = [columns_0, columns_1, columns_2, columns_3, columns_4, columns_5]
    sql_columns = ', '.join([f'{col}.[{val}]' for col, val in columns_list[search_id]])
    django_columns = [f'{col}_{val}' for col, val in columns_list[search_id]]
    # id
    query_0 = f'''
        SELECT TOP ({sql_set}) {sql_columns}
        FROM [oplan3].[dbo].[program] AS Progs
        LEFT JOIN [oplan3].[dbo].[AdultType] AS Adult
            ON Progs.[AdultTypeID] = Adult.[AdultTypeID]
        WHERE Progs.[deleted] = 0
        AND Progs.[program_id] = {search_query}
        ORDER BY Progs.[program_id];
        '''
    # name
    query_1 = f'''
        SELECT TOP ({sql_set}) {sql_columns}
        FROM [oplan3].[dbo].[program] AS Progs
        LEFT JOIN [oplan3].[dbo].[AdultType] AS Adult
            ON Progs.[AdultTypeID] = Adult.[AdultTypeID]
        WHERE Progs.[deleted] = 0
        AND Progs.[DeletedIncludeParent] = 0
        AND Progs.[program_kind] IN (0, 3)
        AND Progs.[program_type_id] NOT IN (1, 2, 3, 9, 13, 14, 15)
        AND (Progs.[name] LIKE '%{search_query}%'
        OR Progs.[AnonsCaption] LIKE '%{search_query}%')
        ORDER BY Progs.[name];
        '''
    # file_name
    query_2 = f'''
        SELECT TOP ({sql_set}) {sql_columns}
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
        AND Progs.[DeletedIncludeParent] = 0
        AND Progs.[program_kind] IN (0, 3)
        AND Progs.[program_type_id] NOT IN (1, 2, 3, 9, 13, 14, 15)
        AND Files.[Name] LIKE '%{search_query}%'
        ORDER BY Files.[Name];
        '''
    # !!!engineer
    query_3 = f'''
        SELECT TOP ({sql_set}) {sql_columns}
        FROM [oplan3].[dbo].[program] AS Progs
        LEFT JOIN [oplan3].[dbo].[ProgramCustomFieldValues] AS Fields
            ON Progs.[program_id] = Fields.[ObjectId]
        LEFT JOIN [planner].[dbo].[task_list] AS Task
            ON Progs.[program_id] = Task.[program_id]
        LEFT JOIN [oplan3].[dbo].[AdultType] AS Adult
            ON Progs.[AdultTypeID] = Adult.[AdultTypeID]
        WHERE Progs.[deleted] = 0
        AND Progs.[DeletedIncludeParent] = 0
        AND Fields.[ProgramCustomFieldId] = 15
        AND Fields.[IntValue] = {search_query}
        OR Task.[engineer_id] = {search_query}
        AND Progs.[program_id] NOT IN
            (SELECT program_id FROM [planner].[dbo].[task_list] WHERE [engineer_id] = {search_query})
        ORDER BY Progs.[program_id];
        '''
    # sched_date
    query_4 = f'''
        SELECT TOP ({sql_set}) {sql_columns}
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
        LEFT JOIN [oplan3].[dbo].[AdultType] AS Adult
            ON Progs.[AdultTypeID] = Adult.[AdultTypeID]
        LEFT JOIN [planner].[dbo].[task_list] AS Task
            ON Progs.[program_id] = Task.[program_id]
        WHERE Files.[Deleted] = 0
        AND Files.[PhysicallyDeleted] = 0
        AND Clips.[Deleted] = 0
        AND Progs.[deleted] = 0
        AND Progs.[DeletedIncludeParent] = 0
        AND SchedProg.[Deleted] = 0
        AND SchedDay.[schedule_id] IN (3, 5, 6, 7, 8, 9, 10, 11, 12, 20)
        AND SchedDay.[day_date] = '{search_query}'
        AND Progs.[program_type_id] IN (4, 5, 6, 7, 8, 10, 11, 12, 16, 17, 18, 19, 20)
        AND Progs.[program_id] > 0
        ORDER BY SchedProg.[DateTime];
        '''
    # last_date
    query_5 = f'''
        SELECT TOP ({sql_set}) {sql_columns}
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
        LEFT JOIN [oplan3].[dbo].[AdultType] AS Adult
            ON Progs.[AdultTypeID] = Adult.[AdultTypeID]
        LEFT JOIN [planner].[dbo].[task_list] AS Task
            ON Progs.[program_id] = Task.[program_id]
        WHERE Files.[Deleted] = 0
        AND Files.[PhysicallyDeleted] = 0
        AND Clips.[Deleted] = 0
        AND Progs.[deleted] = 0
        AND Progs.[DeletedIncludeParent] = 0
        AND SchedProg.[Deleted] = 0
        AND SchedDay.[schedule_id] IN (3, 5, 6, 7, 8, 9, 10, 11, 12, 20)
        AND SchedDay.[day_date] = DATEADD(DAY, -14, '{search_query}')
        AND Progs.[program_type_id] IN (4, 5, 6, 7, 8, 10, 11, 12, 16, 17, 18, 19, 20)
        AND Progs.[program_id] > 0
        ORDER BY SchedProg.[DateTime];
        '''
    query_list = [query_0, query_1, query_2, query_3, query_4, query_5]
    query = query_list[search_id]

    with connections['oplan3'].cursor() as cursor:
        print(query)
        cursor.execute(query)
        result = cursor.fetchall()
    # search_list = [dict(zip(django_columns, task)) for task in result]
    search_list = []
    program_id_list = []
    for program_info in result:
        program_id = program_info[0]
        if program_id in program_id_list:
            continue
        temp_dict = dict(zip(django_columns, program_info))
        if not temp_dict.get('Task_work_date'):
            cenz_info_dict = cenz_info(temp_dict.get('Progs_program_id'))
            temp_dict['work_date'] = cenz_info_dict.get(7)
            temp_dict['engineer_id'] = cenz_info_dict.get(15)
        else:
            print('pass')
        if not temp_dict.get('Adult_Name'):
            temp_dict['Adult_Name'] = parent_adult_name(temp_dict.get('Progs_parent_id'))
        if not temp_dict.get('Files_Name'):
            file_path_info = find_file_path(program_id)
            if file_path_info:
                temp_dict.update(file_path_info)
        program_id_list.append(program_id)
        search_list.append(temp_dict)
    # print(search_list)
    return search_list

def cenz_info(program_id):
    with connections['oplan3'].cursor() as cursor:
        columns = '[ProgramCustomFieldId], [IntValue], [DateValue]'
        query = f'''
        SELECT {columns}
        FROM [oplan3].[dbo].[ProgramCustomFieldValues]
        WHERE [ObjectId] = {program_id}
        AND [ProgramCustomFieldId] IN (7, 15)
        '''
        # print(query)
        cursor.execute(query)
        cenz_info_sql = cursor.fetchall()
    custom_fields_dict = {}
    for cenz in cenz_info_sql:
        field_id, int_value, date_value = cenz
        # Дата отсмотра
        if field_id == 7:
            custom_fields_dict[field_id] = date_value
        elif field_id == 15:
            custom_fields_dict[field_id] = int_value
    return custom_fields_dict

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

def find_file_path(program_id):
    columns = (('Files', 'Name'), ('Files', 'Size'), ('Files', 'CreationTime'),
               ('Files', 'ModificationTime'), ('Progs', 'duration'))
    sql_columns = ', '.join([f'{col}.[{val}]' for col, val in columns])
    django_columns = [f'{col}_{val}' for col, val in columns]
    with connections['oplan3'].cursor() as cursor:
        query = f'''
        SELECT {sql_columns}
        FROM [oplan3].[dbo].[File] AS Files
        JOIN [oplan3].[dbo].[Clip] AS Clips
            ON Files.[ClipID] = Clips.[ClipID]
        JOIN [oplan3].[dbo].[program] AS Progs
            ON Clips.[MaterialID] = Progs.[SuitableMaterialForScheduleID]
        WHERE Files.[Deleted] = 0
        AND Files.[PhysicallyDeleted] = 0
        AND Clips.[Deleted] = 0
        AND Progs.[deleted] = 0
        AND Progs.[DeletedIncludeParent] = 0
        AND Progs.[program_id] = {program_id}
        '''
        cursor.execute(query)
        file_path_info = cursor.fetchone()
    if file_path_info:
        return dict(zip(django_columns, file_path_info))