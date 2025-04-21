from datetime import datetime, date
from types import NoneType

from django.db import connections
from django.template.defaulttags import register

from .ffmpeg_info import collection
from .kinoroom_parser import locate_url
from .db_connection import parent_name, parent_adult_name


@register.filter
def cenz_name(cenz_id):
    if cenz_id:
        cenz_id = int(cenz_id)
    cenz_dict = {
        0: '0+',
        1: '6+',
        2: '12+',
        3: '16+',
        4: '18+'
    }
    return cenz_dict.get(cenz_id)

@register.filter
def engineer_name(engineer_id):
    if engineer_id:
        engineer_id = int(engineer_id)
    engineer_dict = {
        0: 'Александр Кисляков',
        1: 'Ольга Кузовкина',
        2: 'Дмитрий Гатенян',
        3: 'Мария Сучкова',
        4: 'Андрей Антипин',
        5: 'Роман Рогачев',
        6: 'Анастасия Чебакова',
        7: 'Никита Кузаков',
        8: 'Олег Кашежев',
        9: 'Марфа Тарусина',
        10: 'Евгений Доманов',
        11: 'Алексей Шевченко'
    }
    return engineer_dict.get(engineer_id, 'Не назначен')

@register.filter
def worker_name(worker_id):
    if worker_id:
        with connections['oplan3'].cursor() as cursor:
            query = f'SELECT [user_name] FROM [oplan3].[dbo].[user] WHERE [user_id] = {worker_id}'
            cursor.execute(query)
            worker = cursor.fetchone()
            if worker:
                return worker[0]
            else:
                return 'Аноним'
    else:
        return ''

@register.filter
def fields_name(field_id):
    if field_id:
        field_id = int(field_id)
    fields_dict = {
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
    return fields_dict.get(field_id)


def check_data_type(value):
    if isinstance(value, NoneType):
        return None
    elif isinstance(value, datetime) or isinstance(value, date):
        return value.strftime('%Y-%m-%d %H:%M:%S')
    else:
        return str(value)

def check_planner_status(planner_status):
    status_dict = {
        'no_material': 'Материал отсутствует',
        'not_ready': 'Не готов',
        'fix': 'На доработке',
        'ready': 'Отсмотрен',
        'otk': 'Прошёл ОТК',
        'otk_fail': 'НЕ прошёл ОТК',
        'final': 'Готов к эфиру',
        'ready_fail': 'На пересмотр'
    }
    color_dict = {
        'no_material': 'text-danger',
        'not_ready': 'text-primary',
        'fix': 'text-warning',
        'ready': 'text-success',
        'otk': 'text-success',
        'otk_fail': 'text-danger',
        'final': 'text-success',
        'ready_fail': 'text-danger'

    }
    return status_dict.get(planner_status), color_dict.get(planner_status)

def full_info(program_id):
    with connections['oplan3'].cursor() as cursor:
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
            ('Task', 'engineer_id'), ('Task', 'task_status')]

        sql_columns = ', '.join([f'{col}.[{val}]' for col, val in columns])
        django_columns = [f'{col}_{val}' for col, val in columns]
        movie_query = f'''
        SELECT {sql_columns}
        FROM [oplan3].[dbo].[program] AS Progs
        LEFT JOIN [oplan3].[dbo].[AdultType] AS Adult
            ON Progs.[AdultTypeID] = Adult.[AdultTypeID]
        LEFT JOIN [planner].[dbo].[task_list] AS Task
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
        return full_info_dict

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

def find_episodes(program_id):
    with connections['oplan3'].cursor() as cursor:
        episodes_columns = [
            ('Progs', 'program_id'), ('Progs', 'parent_id'), ('Progs', 'name'), ('Progs', 'orig_name'),
            ('Progs', 'DisplayMediumName'), ('Progs', 'duration'), ('Progs', 'episode_num'), ('Task', 'task_status')]
        episodes_sql_columns = ', '.join([f'{col}.[{val}]' for col, val in episodes_columns])
        django_episodes_columns = [f'{col}_{val}' for col, val in episodes_columns]
        episodes_query = f'''
            SELECT {episodes_sql_columns}
            FROM [oplan3].[dbo].[program] AS Progs
            LEFT JOIN [planner].[dbo].[task_list] AS Task
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
    oplan3_cenz_rate = check_data_type(oplan3_cenz_info.get(14))
    oplan3_engineer = check_data_type(oplan3_cenz_info.get(15))

    # planner_ready_date = full_info_dict.get('Task_ready_date')
    planner_status = full_info_dict.get('Task_task_status')
    if planner_status:
        material_status, color = check_planner_status(planner_status)
    else:
        if oplan3_engineer or oplan3_work_date:
            material_status = 'Отсмотрен через Oplan'
            color = 'text-success'
        elif not oplan3_engineer and not oplan3_cenz_rate and not oplan3_work_date:
            material_status = 'Материал из общего пула'
            color = 'text-info'
        else:
            material_status = 'Карточка материала заполнена неверно'
            color = 'text-danger'

    # if oplan3_work_date and oplan3_cenz_rate and oplan3_engineer and not planner_status:
    #     material_status = f'Отсмотрен через Oplan: {oplan3_work_date.strftime("%d.%m.%Y")}'  # oplan3_ready
    #     color = 'text-success'
    # elif oplan3_work_date and oplan3_cenz_rate and oplan3_engineer and planner_status == 'ready':
    #     material_status = f'Отсмотрен: {planner_ready_date.strftime("%d.%m.%Y")}'  # planner_ready
    #     color = 'text-success'
    # elif not oplan3_work_date and not oplan3_cenz_rate and not oplan3_engineer and planner_status == 'not_ready':
    #     material_status = 'Не готов'  # planner_not_ready
    #     color = 'text-danger'
    # elif oplan3_work_date and oplan3_cenz_rate and oplan3_engineer and planner_status == 'fix':
    #     material_status = 'На доработке'  # planner_fix
    #     color = 'text-warning'
    # elif not oplan3_work_date and not oplan3_cenz_rate and not oplan3_engineer and planner_status == 'fix':
    #     material_status = 'На доработке'  # planner_fix
    #     color = 'text-warning'
    # elif not oplan3_work_date and not oplan3_cenz_rate and not oplan3_engineer and not planner_status:
    #     material_status = 'Материал из общего пула'  # planner_fix
    #     color = 'text-info'
    # else:
    #     material_status = 'Карточка материала заполнена неверно'  # planner_fix
    #     color = 'text-danger'
    return material_status, color, oplan3_work_date


def cenz_info(program_id):
    with connections['oplan3'].cursor() as cursor:
        columns = '[ProgramCustomFieldId], [TextValue], [IntValue], [DateValue]'
        query = f'''
            SELECT {columns}
            FROM [oplan3].[dbo].[ProgramCustomFieldValues]
            WHERE [ObjectId] = {program_id}
            '''
        cursor.execute(query)
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
        cursor.execute(query)

def update_value(field_id, program_id, new_value):
    if field_id == 7:
        query = f'''
        UPDATE [oplan3].[dbo].[ProgramCustomFieldValues]
        SET [DateValue] = '{new_value}'
        WHERE [ObjectId] = {program_id}
        AND [ProgramCustomFieldId] = {field_id}
        '''
    elif field_id in (8, 9, 10, 11, 12, 13, 16, 18, 19):
        query = f'''
        UPDATE [oplan3].[dbo].[ProgramCustomFieldValues]
        SET [TextValue] = '{new_value}'
        WHERE [ObjectId] = {program_id}
        AND [ProgramCustomFieldId] = {field_id}
        '''
    elif field_id in (14, 15, 17):
        query = f'''
        UPDATE [oplan3].[dbo].[ProgramCustomFieldValues]
        SET [IntValue] = {new_value}
        WHERE [ObjectId] = {program_id}
        AND [ProgramCustomFieldId] = {field_id}
        '''
    else:
        query = ''

    if query:
        with connections['oplan3'].cursor() as cursor:
            print(query)
            cursor.execute(query)

def update_file_path(program_id, file_path):
    with connections['planner'].cursor() as cursor:
        query = f'''
        UPDATE [planner].[dbo].[task_list]
        SET [file_path] = '{file_path}'
        WHERE [program_id] = {program_id}
        '''
        cursor.execute(query)

def change_task_status(program_id, engineer_id, work_date, task_status):
    with connections['planner'].cursor() as cursor:
        select = f'SELECT [task_status] FROM [planner].[dbo].[task_list] WHERE [program_id] = {program_id}'
        cursor.execute(select)
        if cursor.fetchone():
            update = f'''
            UPDATE [planner].[dbo].[task_list]
            SET [task_status] = {task_status}, [ready_date] = GETDATE()
            WHERE [program_id] = {program_id}'''
            cursor.execute(update)
        else:
            file_path_dict = find_file_path(program_id)
            file_path = file_path_dict.get('Files_Name')
            duration = file_path_dict.get('Progs_duration')

            columns = '[program_id], [engineer_id], [duration], [work_date], [ready_date], [task_status], [file_path]'
            values = (program_id, engineer_id, duration, work_date, 'GETDATE()', task_status, file_path)
            query = f'''
            INSERT INTO [planner].[dbo].[task_list] ({columns})
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            '''
            cursor.execute(query, values)

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

def schedule_info(program_id):
    with connections['oplan3'].cursor() as cursor:
        columns = ['ChannelId', 'ChannelName', 'DateTime']
        sql_columns = ', '.join(columns)
        query = f'''
        SELECT {sql_columns}
        FROM [oplan3].[dbo].[ScheduledInfo]
        WHERE [ProgramId] = {program_id}
        '''
        cursor.execute(query)
        schedule_dict = [dict(zip(columns, schedule)) for schedule in cursor.fetchall()]
    return schedule_dict