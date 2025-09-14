from datetime import datetime, date, timedelta
from types import NoneType

from django.db import connections

from .db_connection import parent_name, parent_adult_name
from .settings.main_set import MainSettings
from planner.settings import OPLAN_DB, PLANNER_DB

def check_data_type(value):
    if isinstance(value, NoneType) or value == '':
        return None
    elif isinstance(value, datetime) or isinstance(value, date):
        return value.strftime('%Y-%m-%d %H:%M:%S')
    else:
        return value

def check_planner_status(planner_status):
    status_dict = MainSettings.status_dict
    return status_dict.get(planner_status)

def check_color_status(planner_status):
    color_dict = MainSettings.color_dict
    return color_dict.get(planner_status)

def full_info(program_id):
    with connections[OPLAN_DB].cursor() as cursor:
        columns = [
            ('Progs', 'program_id'), ('Progs', 'parent_id'), ('Progs', 'program_type_id'), ('Progs', 'program_kind'),
            ('Progs', 'name'), ('Progs', 'orig_name'), ('Progs', 'annotation'), ('Progs', 'duration'),
            ('Progs', 'comment'), ('Progs', 'keywords'), ('Progs', 'anounce_text'), ('Progs', 'episode_num'),
            ('Progs', 'last_edit_user_id'), ('Progs', 'last_edit_time'), ('Progs', 'authors'),
            ('Progs', 'producer'), ('Progs', 'production_year'), ('Progs', 'production_country'),
            ('Progs', 'subject'), ('Progs', 'SourceID'), ('Progs', 'AnonsCaption'),
            ('Progs', 'DisplayMediumName'), ('Progs', 'SourceFileMedium'), ('Progs', 'EpisodesTotal'),
            ('Progs', 'MaterialState'), ('Progs', 'SourceMedium'), ('Progs', 'HasSourceClip'),
            ('Progs', 'AnonsCaptionInherit'), ('Progs', 'CreationDate'), ('Progs', 'Subtitled'), ('Progs', 'Season'),
            ('Progs', 'Director'), ('Progs', 'Cast'), ('Progs', 'MusicComposer'), ('Progs', 'ShortAnnotation'),
            ('Adult', 'Name'), ('Task', 'work_date'), ('Task', 'ready_date'),
            ('Task', 'worker_id'), ('Task', 'task_status')
        ]

        sql_columns = ', '.join([f'{col}.[{val}]' for col, val in columns])
        django_columns = [f'{col}_{val}' for col, val in columns]
        movie_query = f'''
        SELECT {sql_columns}
        FROM [{OPLAN_DB}].[dbo].[program] AS Progs
        LEFT JOIN [{OPLAN_DB}].[dbo].[AdultType] AS Adult
            ON Progs.[AdultTypeID] = Adult.[AdultTypeID]
        LEFT JOIN [{PLANNER_DB}].[dbo].[task_list] AS Task
            ON Progs.[program_id] = Task.[program_id]
        WHERE Progs.[deleted] = 0
        AND Progs.[DeletedIncludeParent] = 0
        AND Progs.[program_id] = {program_id}
        '''
        # AND Progs.[program_type_id] NOT IN (3, 9, 13, 14, 15, 17, 18)

        cursor.execute(movie_query)
        movie_info = cursor.fetchone()

    file_path_info = find_file_path(program_id)
    if movie_info:
        full_info_dict = dict(zip(django_columns, movie_info))
        if file_path_info:
            full_info_dict.update(file_path_info)
        if not full_info_dict.get('Adult_Name'):
            full_info_dict['Adult_Name'] = parent_adult_name(full_info_dict.get('Progs_parent_id'))
        full_info_dict['material_status'], full_info_dict['color'], full_info_dict['oplan3_work_date'] = find_out_status(program_id, full_info_dict)
        if full_info_dict.get('Progs_program_kind') in (1, 4):
            full_info_dict['episodes'] = find_episodes(program_id)

        if full_info_dict['Progs_program_type_id'] in (4, 8, 12, 16): # сериалы
            full_info_dict['material_type'] = 'season'
        else:
            full_info_dict['material_type'] = 'film'
        # print(full_info_dict)
        return full_info_dict

def find_file_path(program_id):
    columns = (('Files', 'FileID'), ('Files', 'Name'), ('Files', 'Size'), ('Files', 'CreationTime'),
               ('Files', 'ModificationTime'), ('Progs', 'duration'))
    sql_columns = ', '.join([f'{col}.[{val}]' for col, val in columns])
    django_columns = [f'{col}_{val}' for col, val in columns]
    with connections[OPLAN_DB].cursor() as cursor:
        query = f'''
        SELECT {sql_columns}
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
        AND Progs.[program_id] = {program_id}
        '''
        cursor.execute(query)
        file_path_info = cursor.fetchone()
    if file_path_info:
        return dict(zip(django_columns, file_path_info))

def find_episodes(program_id):
    with connections[OPLAN_DB].cursor() as cursor:
        episodes_columns = [
            ('Progs', 'program_id'), ('Progs', 'parent_id'), ('Progs', 'name'), ('Progs', 'orig_name'),
            ('Progs', 'DisplayMediumName'), ('Progs', 'duration'), ('Progs', 'episode_num'), ('Task', 'task_status')]
        episodes_sql_columns = ', '.join([f'{col}.[{val}]' for col, val in episodes_columns])
        django_episodes_columns = [f'{col}_{val}' for col, val in episodes_columns]
        episodes_query = f'''
            SELECT {episodes_sql_columns}
            FROM [{OPLAN_DB}].[dbo].[program] AS Progs
            LEFT JOIN [{PLANNER_DB}].[dbo].[task_list] AS Task
                ON Progs.[program_id] = Task.[program_id]
            WHERE Progs.[deleted] = 0
            AND Progs.[DeletedIncludeParent] = 0
            AND Progs.[parent_id] = {program_id}
            ORDER BY Progs.[episode_num]
            '''
        cursor.execute(episodes_query)
        episodes_info = cursor.fetchall()
        if episodes_info:
            return [dict(zip(django_episodes_columns, episodes)) for episodes in episodes_info]

def find_out_status(program_id, full_info_dict):
    oplan3_cenz_info = cenz_info(program_id)
    oplan3_work_date = oplan3_cenz_info.get(7)
    oplan3_cenz_rate = oplan3_cenz_info.get(14)
    oplan3_engineer_id = oplan3_cenz_info.get(15)

    # planner_ready_date = full_info_dict.get('Task_ready_date')
    planner_status = full_info_dict.get('Task_task_status')
    if planner_status:
        material_status = check_planner_status(planner_status)
        color = check_color_status(planner_status)
    else:
        if oplan3_engineer_id is not None or oplan3_work_date:
            material_status = 'Отсмотрен через Oplan'
            color = 'text-success'
        elif oplan3_engineer_id is None and oplan3_cenz_rate is None and oplan3_work_date is None:
            material_status = 'Материал из общего пула'
            color = 'text-info'
        else:
            material_status = 'Карточка материала заполнена неверно'
            color = 'text-danger'
    return material_status, color, oplan3_work_date


def cenz_info(program_id):
    with connections[OPLAN_DB].cursor() as cursor:
        columns = '[ProgramCustomFieldId], [TextValue], [IntValue], [DateValue]'
        query = f'''
            SELECT {columns}
            FROM [{OPLAN_DB}].[dbo].[ProgramCustomFieldValues]
            WHERE [ObjectId] = {program_id}
            '''
        cursor.execute(query)
        cenz_info_sql = cursor.fetchall()
    custom_fields_dict = {}
    for cenz in cenz_info_sql:
        field_id, text_value, int_value, date_value = cenz
        # Дата отсмотра
        if field_id == 7:
            custom_fields_dict[field_id] = date_value.strftime('%Y-%m-%d')
        elif field_id in (8, 9, 10, 11, 12, 13, 16, 18, 19):
            custom_fields_dict[field_id] = text_value
        elif field_id in (14, 15, 17, 22):
            custom_fields_dict[field_id] = int_value
    return custom_fields_dict


def insert_value(field_id, program_id, new_value):
    if field_id in (17, 22) and new_value == '0':
        return
    if field_id == 7:
        columns = '[ProgramCustomFieldId], [ObjectId], [DateValue], [ObjectType]'
    elif field_id in (8, 9, 10, 11, 12, 13, 16, 18, 19):
        columns = '[ProgramCustomFieldId], [ObjectId], [TextValue], [ObjectType]'
    elif field_id in (14, 15, 17, 22):
        columns = '[ProgramCustomFieldId], [ObjectId], [IntValue], [ObjectType]'
    else:
        columns = ''

    if columns:
        with connections[OPLAN_DB].cursor() as cursor:
            query = f'''
            INSERT INTO [{OPLAN_DB}].[dbo].[ProgramCustomFieldValues]
            ({columns})
            VALUES
            (%s, %s, %s, %s)
            '''
            cursor.execute(query, (field_id, program_id, new_value, 0))

def delete_value(field_id, program_id):
    print('delete', field_id)
    with connections[OPLAN_DB].cursor() as cursor:
        query = f'''
        DELETE FROM [{OPLAN_DB}].[dbo].[ProgramCustomFieldValues]
        WHERE [ObjectId] = {program_id}
        AND [ProgramCustomFieldId] = {field_id}
        '''
        cursor.execute(query)
        return cursor.rowcount

def update_value(field_id, program_id, new_value):
    print('update', field_id, new_value)
    query = ''
    if field_id == 7:
        query = f'''
        UPDATE [{OPLAN_DB}].[dbo].[ProgramCustomFieldValues]
        SET [DateValue] = '{new_value}'
        WHERE [ObjectId] = {program_id}
        AND [ProgramCustomFieldId] = {field_id}
        '''
    elif field_id in (8, 9, 10, 11, 12, 13, 16, 18, 19):
        query = f'''
        UPDATE [{OPLAN_DB}].[dbo].[ProgramCustomFieldValues]
        SET [TextValue] = '{new_value}'
        WHERE [ObjectId] = {program_id}
        AND [ProgramCustomFieldId] = {field_id}
        '''
    elif field_id in (14, 15, 17, 22):
        query = f'''
        UPDATE [{OPLAN_DB}].[dbo].[ProgramCustomFieldValues]
        SET [IntValue] = {new_value}
        WHERE [ObjectId] = {program_id}
        AND [ProgramCustomFieldId] = {field_id}
        '''
    if query:
        with connections[OPLAN_DB].cursor() as cursor:
            cursor.execute(query)
            return cursor.rowcount

def update_file_path(program_id, file_path):
    if file_path:
        if file_path.startswith('"') and file_path.endswith('"'):
            file_path = file_path[1:-1]
        with connections[PLANNER_DB].cursor() as cursor:
            query = f'''
            UPDATE [{PLANNER_DB}].[dbo].[task_list]
            SET [file_path] = '{file_path}'
            WHERE [program_id] = {program_id}
            '''
            cursor.execute(query)
            return cursor.rowcount
    else:
        return 'Новый путь не указан'

def change_db_cenz_info(service_info_dict, old_values_dict, new_values_dict):
    program_id = service_info_dict.get('program_id')
    for old_field_id, new_field_id in zip(old_values_dict, new_values_dict):
        old_value, new_value = old_values_dict.get(old_field_id), new_values_dict.get(new_field_id)
        old_value, new_value = check_data_type(old_value), check_data_type(new_value)
        if not old_value and new_value:
            insert_value(new_field_id, program_id, new_value)
        elif old_value and not new_value:
            delete_value(old_field_id, program_id)
        elif old_value and new_value and str(old_value) != str(new_value):
            update_value(old_field_id, program_id, new_value)
            
def change_oplan_cenz_info(program_id, old_values, new_values):
    values_list = (
        (17, 'meta_form'),
        (7, 'work_date_form'),
        (14, 'cenz_rate_form'),
        (15, 'engineers_form'),
        (18, 'tags_form'),
        (19, 'inoagent_form'),
        (22, 'narc_select_form'),
        (8, 'lgbt_form'),
        (9, 'sig_form'),
        (10, 'obnazh_form'),
        (11, 'narc_form'),
        (12, 'mat_form'),
        (13, 'other_form'),
        (16, 'editor_form')
    )
    for num_key, name_key in values_list:
        old_value, new_value = old_values.get(num_key), new_values.get(name_key)
        old_value, new_value = check_data_type(old_value), check_data_type(new_value)
        # print(num_key, name_key, 'old_value:', old_value, 'new_value:', new_value)
        if old_value is None and new_value is not None:
            insert_value(num_key, program_id, new_value)
        elif old_value is not None and new_value is None:
            delete_value(num_key, program_id)
        elif old_value is not None and new_value is not None and str(old_value) != str(new_value):
            update_value(num_key, program_id, new_value)


def schedule_info(program_id):
    with connections[OPLAN_DB].cursor() as cursor:
        columns = ['ChannelId', 'ChannelName', 'DateTime']
        sql_columns = ', '.join(columns)
        query = f'''
        SELECT {sql_columns}
        FROM [{OPLAN_DB}].[dbo].[ScheduledInfo]
        WHERE [ProgramId] = {program_id}
        '''
        cursor.execute(query)
        schedule_dict = [dict(zip(columns, schedule)) for schedule in cursor.fetchall()]
    return schedule_dict

def calc_otk_deadline():
    # with connections[PLANNER_DB].cursor() as cursor:
    #     cursor.execute(f'SELECT day_off FROM [{PLANNER_DB}].[dbo].[days_off] WHERE day_off = "{work_day}"')
    #     day_off = cursor.fetchone()
    # deadline = date.today()
    # for day in range(5):
    #     if deadline != day_off:
    #         deadline += timedelta(days=1)
    return date.today() + timedelta(days=5)

def comments_history(program_id):
    with connections[PLANNER_DB].cursor() as cursor:
        columns = 'task_status', 'worker_id', 'comment', 'deadline', 'time_of_change'
        sql_columns = ', '.join(columns)
        query = f'''
        SELECT {sql_columns}
        FROM [{PLANNER_DB}].[dbo].[comments_history]
        WHERE program_id = {program_id}
        ORDER BY [time_of_change]
        '''
        cursor.execute(query)
        return [dict(zip(columns, val)) for val in cursor.fetchall()]

def unblock_object(program_id, worker_id):
    with connections[OPLAN_DB].cursor() as cursor:
        query = f'''
        DELETE FROM [{OPLAN_DB}].[dbo].[ObjectLock]
        WHERE [ObjectID] = {program_id}
        AND [UserID] = {worker_id}'''
        cursor.execute(query)
        return cursor.rowcount

def insert_filepath_history(program_id, worker_id, task_status, comment, time_of_change):
    with connections[PLANNER_DB].cursor() as cursor:
        values = (program_id, worker_id, task_status, comment, time_of_change)
        query = f'''
        INSERT INTO [{PLANNER_DB}].[dbo].[filepath_history]
        (program_id, worker_id, task_status, comment, time_of_change)
        VALUES (%s, %s, %s, %s, %s)
        '''
        cursor.execute(query, values)
        return cursor.rowcount

def select_filepath_history(program_id):
    with connections[PLANNER_DB].cursor() as cursor:
        columns = 'program_id', 'file_path', 'task_status', 'time_of_change'
        sql_columns = ', '.join(columns)
        query = f'SELECT {sql_columns} FROM [{PLANNER_DB}].[dbo].[filepath_history] WHERE [program_id] = {program_id}'
        cursor.execute(query)
        return [dict(zip(columns, val)) for val in cursor.fetchall()]