from django.db import connections

from .ffmpeg_info import collection
from .kinoroom_parser import locate_url
from .db_connection import parent_name


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
                   ('Files', 'CreationTime'), ('Files', 'ModificationTime'), ('TaskInf', 'work_date'),
                   ('TaskInf', 'ready_date'), ('TaskInf', 'worker_id'), ('TaskInf', 'worker'), ('TaskInf', 'task_status')]

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
            LEFT JOIN [planner].[dbo].[task_list] AS TaskInf
                ON Progs.[program_id] = TaskInf.[program_id]
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
        # full_info_dict['custom_fields'] = cenz_info(program_id)
        # full_info_dict['schedule_info'] = schedule_info(program_id)
        if full_info_dict['Progs_program_type_id'] in (4, 8, 12): # сериалы
            poster_link = locate_url(
                full_info_dict.get('Progs_parent_id'),
                parent_name(full_info_dict.get('Progs_parent_id')),
                full_info_dict.get('Progs_production_year'))
            full_info_dict['poster_link'] = poster_link
        else:
            poster_link = locate_url(
                full_info_dict.get('Progs_program_id'),
                full_info_dict.get('Progs_AnonsCaption'),
                full_info_dict.get('Progs_production_year'))

            full_info_dict['poster_link'] = poster_link

            oplan3_cenz_info = cenz_info(program_id)
            oplan3_work_date = oplan3_cenz_info.get(7)
            oplan3_cenz_rate = oplan3_cenz_info.get(14)
            oplan3_cenz_worker_id = oplan3_cenz_info.get('worker_id')
            oplan3_cenz_worker = oplan3_cenz_info.get(15)

            planner_ready_date = full_info_dict.get('TaskInf_ready_date')
            planner_status = full_info_dict.get('TaskInf_task_status')

            if oplan3_work_date and oplan3_cenz_rate and oplan3_cenz_worker and not planner_status:
                full_info_dict['material_status'] = f'Материал отсмотрен через Oplan: {oplan3_work_date.strftime('%d.%m.%Y')}' # oplan3_ready
                full_info_dict['color'] = 'text-success'
            elif oplan3_work_date and oplan3_cenz_rate and oplan3_cenz_worker and planner_status:
                full_info_dict['material_status'] = f'Материал отсмотрен: {planner_ready_date.strftime('%d.%m.%Y')}' # planner_ready
                full_info_dict['color'] = 'text-success'
            elif not oplan3_work_date and not oplan3_cenz_rate and not oplan3_cenz_worker and planner_status =='not_ready':
                full_info_dict['material_status'] = 'Материал не готов' # planner_not_ready
                full_info_dict['color'] = 'text-danger'
            elif oplan3_work_date and oplan3_cenz_rate and oplan3_cenz_worker and planner_status == 'fix':
                full_info_dict['material_status'] = 'Материал на доработке' # planner_fix
                full_info_dict['color'] = 'text-warning'
            elif not oplan3_work_date and not oplan3_cenz_rate and not oplan3_cenz_worker and planner_status == 'fix':
                full_info_dict['material_status'] = 'Материал на доработке' # planner_fix
                full_info_dict['color'] = 'text-warning'
            print('planner_status', planner_status)
        return full_info_dict

def cenz_info(program_id):
    with connections['oplan3'].cursor() as cursor:
        columns = '[ProgramCustomFieldId], [TextValue], [IntValue], [DateValue]'
        query_test = f'''
            SELECT {columns}
            FROM [oplan3].[dbo].[ProgramCustomFieldValues]
            WHERE [ObjectId] = {program_id}
                '''
        cursor.execute(query_test)
        cenz_info_sql = cursor.fetchall()
        custom_fields_dict = {}
        for cenz in cenz_info_sql:
            field_id, text_value, int_value, date_value = cenz
            # Дата отсмотра
            if field_id == 7:
                custom_fields_dict[field_id] = date_value
            elif field_id in (8, 9, 10, 11, 12, 13, 16, 18, 19):
                custom_fields_dict[field_id] = text_value
            elif field_id in (14, 15, 17):
                # custom_fields_dict[field_id] = items_string.split('\r\n')[int_value]
                custom_fields_dict[field_id] = int_value
                # .split(';')
    return custom_fields_dict

def insert_cenz_info():
    fields_id_dict = {
        5: 'Краткое описание',
        7: 'Дата отсмотра',
        8: 'ЛГБТ',
        9: 'Сигареты',
        10: 'Обнаженка',
        11: 'Наркотики',
        12: 'Мат',
        13: 'Другое',
        14: 'Ценз отсмотра',
        15: 'Тайтл проверил',
        16: 'Редакторские замечания',
        17: 'Meta',
        18: 'Теги',
        19: 'Иноагент'}

def insert_value(field_id, program_id, new_value):
    if field_id == 7:
        columns = '[ProgramCustomFieldId], [ObjectId], [DateValue], [ObjectType]'
    elif field_id in (8, 9, 10, 11, 12, 13, 16, 18, 19):
        columns = '[ProgramCustomFieldId], [ObjectId], [TextValue], [ObjectType]'
    elif field_id in (14, 15, 17):
        columns = '[ProgramCustomFieldId], [ObjectId], [IntValue], [ObjectType]'
    else:
        columns = ''

    if columns:
        with connections['oplan3'].cursor() as cursor:
            query = f'''
            INSERT INTO [oplan3].[dbo].[ProgramCustomFieldValues]
            ({columns})
            VALUES
            ({field_id}, {program_id}, '{new_value}', 0)
            '''
            print('insert', query)
            cursor.execute(query)

def delete_value(field_id, program_id):
    with connections['oplan3'].cursor() as cursor:
        query = f'''
        DELETE FROM [oplan3].[dbo].[ProgramCustomFieldValues]
        WHERE [ObjectId] = {program_id}
        AND [ProgramCustomFieldId] = {field_id}
        '''
        print('delete', query)
        cursor.execute(query)

def update_value(field_id, program_id, old_value, new_value):
    if field_id == 7:
        query = f'''
        UPDATE [oplan3].[dbo].[ProgramCustomFieldValues]
        SET [DateValue] = '{new_value}'
        WHERE [ObjectId] = {program_id}
        AND [ProgramCustomFieldId] = {field_id}
        '''
        print('upd date query', query)
    elif field_id in (8, 9, 10, 11, 12, 13, 16, 18, 19):
        query = f'''
        UPDATE [oplan3].[dbo].[ProgramCustomFieldValues]
        SET [TextValue] = '{new_value}'
        WHERE [ObjectId] = {program_id}
        AND [ProgramCustomFieldId] = {field_id}
        AND [TextValue] = '{old_value}'
        '''
        print('upd text query', query)
    elif field_id in (14, 15, 17):
        query = f'''
        UPDATE [oplan3].[dbo].[ProgramCustomFieldValues]
        SET [IntValue] = {new_value}
        WHERE [ObjectId] = {program_id}
        AND [ProgramCustomFieldId] = {field_id}
        AND [IntValue] = {old_value}
        '''
        print('upd int query', query)
    else:
        query = ''

    if query:
        with connections['oplan3'].cursor() as cursor:
            cursor.execute(query)

def change_db_cenz_info(service_info_dict, old_values_dict, new_values_dict):
    print('old_dict', old_values_dict, '\n', 'new_dict', new_values_dict)
    program_id = service_info_dict.get('program_id')
    for old_field_id, new_field_id in zip(old_values_dict, new_values_dict):
        old_value, new_value = old_values_dict.get(old_field_id), new_values_dict.get(new_field_id)
        if old_value == 0:
            old_value = '0'
        if new_value == 0:
            new_value = '0'
        if not old_value and new_value:
            insert_value(new_field_id, program_id, new_value)
        elif old_value and not new_value:
            delete_value(old_field_id, program_id)
        elif old_value and new_value and str(old_value) != str(new_value):
            update_value(old_field_id, program_id, old_value, new_value)

    # with connections['oplan3'].cursor() as cursor:
    #     query = f'''
    #     DELETE FROM [oplan3].[dbo].[ProgramCustomFieldValues] WHERE [program_id] = {kwargs.get('program_id')}
    #
    #     INSERT INTO [oplan3].[dbo].[ProgramCustomFieldValues]
    #     ([worker_id], [worker], [start_date], [end_date], [description])
    #     VALUES ({worker_id}, '{worker}', '{start_date}', '{end_date}', '{description}');
    #     '''
    #
    #     ok = cursor.execute(query)
    #     if ok:
    #         # next
    #         cursor.execute(query)


    # drop
    # insert


    # with connections['oplan3'].cursor() as cursor:
    #     columns = 'Val.[ProgramCustomFieldId], Fields.[Name], Val.[TextValue], Fields.[ItemsString], Val.[IntValue], Val.[DateValue]'
    #     query_test = f'''
    #         UPDATE [oplan3].[dbo].[ProgramCustomFieldValues]
    #         SET [TextValue], Val.[IntValue], Val.[DateValue]
    #         WHERE Val.[ObjectId] = {program_id}
    #         AND [ProgramCustomFieldId] = {field_id}
    #             '''
    #     cursor.execute(query_test)
    #     cenz_info_sql = cursor.fetchall()
    #     custom_fields_dict = {}
    #     for cenz in cenz_info_sql:
    #         field_id, field_name, text_value, items_string, int_value, date_value = cenz
    #         # Ценз отсмотра
    #         if field_id == 14:
    #             custom_fields_dict[field_id] = items_string.split('\r\n')[int_value]
    #         # Тайтл проверил
    #         elif field_id == 15:
    #             custom_fields_dict['worker_id'] = int_value
    #             custom_fields_dict[field_id] = items_string.split('\r\n')[int_value]
    #         # Дата отсмотра
    #         elif field_id == 7:
    #             custom_fields_dict[field_id] = date_value
    #         else:
    #             custom_fields_dict[field_id] = text_value
    # return custom_fields_dict

def schedule_info(program_id):
    with connections['oplan3'].cursor() as cursor:
        columns = ['ChannelId', 'ChannelName', 'DateTime']
        sql_columns = ', '.join(columns)
        query = f'''SELECT {sql_columns}
          FROM [oplan3].[dbo].[ScheduledInfo]
          WHERE [ProgramId] = {program_id}'''
        cursor.execute(query)
        schedule_dict = [dict(zip(columns, schedule)) for schedule in cursor.fetchall()]
    return schedule_dict