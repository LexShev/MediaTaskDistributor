from django.db import connections

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
                full_info_dict['material_status'] = f'Материал отсмотрен в Oplan: {str(oplan3_work_date)}' # oplan3_ready
                full_info_dict['color'] = 'text-success'
            elif oplan3_work_date and oplan3_cenz_rate and oplan3_cenz_worker and planner_status:
                full_info_dict['material_status'] = f'Материал отсмотрен: {str(planner_ready_date)}' # planner_ready
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
            field_id, field_name, text_value, items_string, int_value, date_value = cenz
            # Ценз отсмотра
            if field_id == 14:
                custom_fields_dict[field_id] = items_string.split('\r\n')[int_value]
            # Тайтл проверил
            elif field_id == 15:
                custom_fields_dict['worker_id'] = int_value
                custom_fields_dict[field_id] = items_string.split('\r\n')[int_value]
            # Дата отсмотра
            elif field_id == 7:
                custom_fields_dict[field_id] = date_value
            else:
                custom_fields_dict[field_id] = text_value
    return custom_fields_dict

def insert_cenz_info(**kwargs):
    print(insert_cenz_info_dict)

    with connections['oplan3'].cursor() as cursor:
        query = f'''DELETE FROM [oplan3].[dbo].[ProgramCustomFieldValues] WHERE [program_id] = {kwargs.get('program_id')}
        INSERT INTO [oplan3].[dbo].[ProgramCustomFieldValues]
        ([worker_id], [worker], [start_date], [end_date], [description])
        VALUES ({worker_id}, '{worker}', '{start_date}', '{end_date}', '{description}');
        '''

        ok = cursor.execute(query)
        if ok:
            # next
            cursor.execute(query)


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