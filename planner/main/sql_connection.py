from django.db import connections

def distribution(program_id):
    return 'Александр Кисляков'

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
        if temp_dict['Progs_program_type_id'] in (4, 8, 12):
            if temp_dict['worker']:
                worker = temp_dict['worker']
            else:
                worker = distribution(program_id)
            repeat_index = repeat_index_search(material_list, temp_dict)
            print(repeat_index)
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
                                 'worker': worker}]}
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
                    'worker': worker})
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
                'status': 'ready'}
            if temp_dict['worker']:
                program_info_dict['worker'] = temp_dict['worker']
            else:
                program_info_dict['worker'] = distribution(program_id)
            program_id_list.append(program_id)
            material_list.append(program_info_dict)
    print('material_list', material_list)

    return material_list

def oplan_material_list():
    with connections['oplan3'].cursor() as cursor:
        dates = ('2024-02-16', '2024-02-16')
        # channels = (channels, 'Крепкое')
        channels = ('Кино +', 'Романтичный сериал')
        order = 'ASC'

        field_val_columns = '[ProgramCustomFieldValuesID], [ProgramCustomFieldId], [ObjectId], [TextValue], [IntValue], [DateValue], [ObjectType], [TimeStamp]'
        fields_name_columns = '[CustomFieldID], [Name], [FieldType], [ItemsString], [Position], [ObjectType], [TimeStamp]'

        file_columns = ('Name', 'Size', 'CreationTime', 'ModificationTime')
        program_columns = ('program_id', 'parent_id', 'program_type_id', 'name', 'orig_name', 'annotation', 'duration', 'comment',
                           'keywords', 'anounce_text', 'episode_num', 'last_edit_user_id',
                           'last_edit_time', 'authors', 'producer', 'production_year', 'production_country',
                           'subject', 'SourceID', 'AnonsCaption', 'DisplayMediumName', 'SourceFileMedium',
                           'EpisodesTotal', 'MaterialState', 'SourceMedium', 'HasSourceClip', 'AnonsCaptionInherit',
                           'AdultTypeID', 'CreationDate', 'Subtitled', 'Season', 'Director', 'Cast',
                           'MusicComposer', 'ShortAnnotation')

        sql_columns = ', '.join(
            [f'Progs.[{col}]' for col in program_columns] + [f'Files.[{col}]' for col in file_columns] + [
                'Types.[type_name]', 'SchedDay.[day_date]', 'Sched.[schedule_name]', 'worker'])
        django_columns = [f'Progs_{col}' for col in program_columns] + [f'Files_{col}' for col in file_columns] + [
            'Types_type_name', 'SchedDay_day_date', 'Sched_schedule_name', 'worker']
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
        return material_list


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
        cenz_info_list = []
        for cenz in cenz_info_sql:
            cenz_info_dict = {}
            field_id, field_name, text_value, items_string, int_value, data_value = cenz
            if field_id == 5:
                cenz_info_dict['field_id'] = field_id
                cenz_info_dict['value'] = text_value
            elif field_id == 14 or field_id == 15:
                cenz_info_dict['field_id'] = field_id
                cenz_info_dict['value'] = items_string.split('\r\n')[int_value]
            elif field_id == 7:
                cenz_info_dict['field_id'] = field_id
                cenz_info_dict['value'] = data_value
            cenz_info_list.append(cenz_info_dict)
        return cenz_info_list