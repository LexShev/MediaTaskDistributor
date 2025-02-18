from django.db import connections


def distribution(program_id):
    return 0, 'Александр Кисляков'

def repeat_index_search(material_list, temp_dict):
    for num, program in enumerate(material_list):
        if temp_dict['Progs_parent_id'] == program['Progs_parent_id']:
            return num

def make_material_list(material_list_sql, django_columns):
    material_list = []
    program_id_list = []
    for program_info in material_list_sql:
        if not program_info:
            continue
        program_id = program_info[0]
        if program_id in program_id_list:
            continue
        temp_dict = dict(zip(django_columns, program_info))
        print(temp_dict)
        if temp_dict['Progs_program_type_id'] in (4, 5, 6, 10, 11, 12) and not temp_dict['DopInf_worker']:
            worker_id, worker = distribution(program_id)
        else:
            worker_id = temp_dict['DopInf_worker_id']
            worker = temp_dict['DopInf_worker']

        if temp_dict['Progs_program_type_id'] in (4, 8, 12):
            repeat_index = repeat_index_search(material_list, temp_dict)
            if not repeat_index and repeat_index != 0:
                program_info_dict = {
                    'Progs_parent_id': temp_dict['Progs_parent_id'],
                    'Progs_AnonsCaption': temp_dict['Progs_AnonsCaption'],
                    'Progs_production_year': temp_dict['Progs_production_year'],
                    'type': 'season',
                    'episode': [{'Progs_program_id': temp_dict['Progs_program_id'],
                                 'Progs_name': temp_dict['Progs_name'],
                                 'Progs_episode_num': temp_dict['Progs_episode_num'],
                                 'Sched_schedule_name': temp_dict['Sched_schedule_name'],
                                 'SchedDay_day_date': temp_dict['SchedDay_day_date'],
                                 'status': 'ready',
                                 'DopInf_worker_id': worker_id,
                                 'DopInf_worker': worker}]}
                program_id_list.append(program_id)
                material_list.append(program_info_dict)
            else:
                material_list[repeat_index]['episode'].append(
                    {'Progs_program_id': temp_dict['Progs_program_id'],
                    'Progs_name': temp_dict['Progs_name'],
                    'Progs_episode_num': temp_dict['Progs_episode_num'],
                    'Sched_schedule_name': temp_dict['Sched_schedule_name'],
                    'SchedDay_day_date': temp_dict['SchedDay_day_date'],
                    'status': 'ready',
                    'DopInf_worker_id': worker_id,
                    'DopInf_worker': worker})
                program_id_list.append(program_id)
        if not temp_dict['Progs_program_type_id'] in (4, 8, 12):
            program_info_dict = {
                'Progs_program_id': temp_dict['Progs_program_id'],
                'Progs_parent_id': temp_dict['Progs_parent_id'],
                'Progs_name': temp_dict['Progs_name'],
                'Progs_production_year': temp_dict['Progs_production_year'],
                'Sched_schedule_name': temp_dict['Sched_schedule_name'],
                'SchedDay_day_date': temp_dict['SchedDay_day_date'],
                'type': 'film',
                'status': 'ready',
                'DopInf_worker_id': worker_id,
                'DopInf_worker': worker}
            program_id_list.append(program_id)
            material_list.append(program_info_dict)
    return material_list

def oplan_material_list():
    with connections['oplan3'].cursor() as cursor:
        dates = ('2024-02-15', '2024-02-16')
        channels = ('Кино +', 'Романтичный сериал', 'Крепкое')
        order = 'ASC'

        columns = [('Progs', 'program_id'), ('Progs', 'parent_id'), ('Progs', 'program_type_id'), ('Progs', 'name'),
                   ('Progs', 'production_year'), ('Progs', 'AnonsCaption'), ('Progs', 'episode_num'),
                   ('Sched', 'schedule_name'), ('SchedDay', 'day_date'), ('DopInf', 'worker_id'), ('DopInf', 'worker')]
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
            LEFT JOIN [planner].[dbo].[dop_info] AS DopInf
                ON Progs.[program_id] = DopInf.[program_id]
            WHERE Files.[Deleted] = 0
            AND Files.[PhysicallyDeleted] = 0
            AND Clips.[Deleted] = 0
            AND Progs.[deleted] = 0
            AND Progs.[program_type_id] NOT IN (3, 9, 13, 14, 15, 17, 18)
            AND Progs.[program_id] > 0
            ORDER BY SchedProg.[DateTime] {order}
                    '''
        cursor.execute(query)
        material_list_sql = cursor.fetchall()
        material_list = make_material_list(material_list_sql, django_columns)
        print('\t', material_list)
        return material_list

def full_info(program_id):
    with connections['oplan3'].cursor() as cursor:
        columns = [('Progs', 'program_id'), ('Progs', 'parent_id'), ('Progs', 'program_type_id'), ('Progs', 'name'),
                   ('Progs', 'orig_name'), ('Progs', 'annotation'), ('Progs', 'duration'), ('Progs', 'comment'),
                   ('Progs', 'keywords'), ('Progs', 'anounce_text'), ('Progs', 'episode_num'),
                   ('Progs', 'last_edit_user_id'), ('Progs', 'last_edit_time'), ('Progs', 'authors'),
                   ('Progs', 'producer'), ('Progs', 'production_year'), ('Progs', 'production_country'),
                   ('Progs', 'subject'), ('Progs', 'SourceID'), ('Progs', 'AnonsCaption'),
                   ('Progs', 'DisplayMediumName'), ('Progs', 'SourceFileMedium'), ('Progs', 'EpisodesTotal'),
                   ('Progs', 'MaterialState'), ('Progs', 'SourceMedium'), ('Progs', 'HasSourceClip'),
                   ('Progs', 'AnonsCaptionInherit'), ('Progs', 'AdultTypeID'), ('Progs', 'CreationDate'),
                   ('Progs', 'Subtitled'), ('Progs', 'Season'), ('Progs', 'Director'), ('Progs', 'Cast'),
                   ('Progs', 'MusicComposer'), ('Progs', 'ShortAnnotation'), ('Files', 'Name'), ('Files', 'Size'),
                   ('Files', 'CreationTime'), ('Files', 'ModificationTime'), ('DopInf', 'worker_id'), ('DopInf', 'worker')]

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
            LEFT JOIN [planner].[dbo].[dop_info] AS DopInf
                ON Progs.[program_id] = DopInf.[program_id]
            WHERE Files.[Deleted] = 0
            AND Files.[PhysicallyDeleted] = 0
            AND Clips.[Deleted] = 0
            AND Progs.[deleted] = 0
            AND Progs.[program_type_id] NOT IN (3, 9, 13, 14, 15, 17, 18)
            AND Progs.[program_id] = {program_id}
                '''
        cursor.execute(query)
        full_info_list = cursor.fetchone()
        # [info.replace('\n', '') for info in full_info_list if isinstance(info, str)]
        full_info_dict = dict(zip(django_columns, full_info_list))
        full_info_dict['custom_fields'] = cenz_info(program_id)
        full_info_dict['schedule_info'] = schedule_info(program_id)
        print('\t', full_info_dict)
        return full_info_dict

def cenz_worker(program_id):
    with connections['oplan3'].cursor() as cursor:
        columns = 'Val.[IntValue], Fields.[ItemsString]'
        query_test = f'''
            SELECT {columns}
            FROM [oplan3].[dbo].[ProgramCustomFields] AS Fields
            JOIN [oplan3].[dbo].[ProgramCustomFieldValues] AS Val
                ON Fields.[CustomFieldID] = Val.[ProgramCustomFieldId]
            WHERE Val.[ObjectId] = {program_id}
            AND Val.[ProgramCustomFieldId] = 15
                '''
        cursor.execute(query_test)
        int_value, items_string = cursor.fetchone()
        custom_fields_dict = {'DopInf_worker_id': int_value,
                              'DopInf_worker': items_string.split('\r\n')[int_value]}
    return custom_fields_dict

def cenz_info(program_id):
    with connections['oplan3'].cursor() as cursor:
        columns = 'Val.[ProgramCustomFieldId], Fields.[Name], Val.[TextValue], Fields.[ItemsString], Val.[IntValue], Val.[DateValue]'
        query_test = f'''
            SELECT {columns}
            FROM [oplan3].[dbo].[ProgramCustomFields] AS Fields
            JOIN [oplan3].[dbo].[ProgramCustomFieldValues] AS Val
                ON Fields.[CustomFieldID] = Val.[ProgramCustomFieldId]
            WHERE Val.[ObjectId] = {program_id}
                '''
        cursor.execute(query_test)
        cenz_info_sql = cursor.fetchall()
        custom_fields_dict = {}
        for cenz in cenz_info_sql:
            field_id, field_name, text_value, items_string, int_value, data_value = cenz
            if field_id == 14:
                custom_fields_dict[field_id] = items_string.split('\r\n')[int_value]
            elif field_id == 15:
                custom_fields_dict['worker_id'] = int_value
                custom_fields_dict[field_id] = items_string.split('\r\n')[int_value]
            elif field_id == 7:
                custom_fields_dict[field_id] = data_value
            else:
                custom_fields_dict[field_id] = text_value
    return custom_fields_dict

def schedule_info(program_id):
    with connections['oplan3'].cursor() as cursor:
        columns = ['ChannelId', 'ChannelName', 'DateTime']
        sql_columns = ', '.join(columns)
        query = f'''SELECT {sql_columns}
          FROM [oplan3].[dbo].[ScheduledInfo]
          WHERE [ProgramId] = {program_id}'''
        cursor.execute(query)
        schedule_list = cursor.fetchall()
        schedule_dict = [dict(zip(columns, schedule)) for schedule in schedule_list]
    return schedule_dict