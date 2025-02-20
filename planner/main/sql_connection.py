from datetime import datetime, timedelta

from django.db import connections


def kpi_worker(worker_id, date):
    with connections['planner'].cursor() as cursor:
        query = f'''SELECT SUM([duration])/8.0
        FROM [planner].[dbo].[task_list]
        WHERE [worker_id] = {worker_id}
        AND [datetime] = {date}
        AND [status] = 'ready'
        AND [vacation] = 0'''
        cursor.execute(query)
        kpi_w = cursor.fetchone()
    return kpi_w


def kpi_min(date):
    with connections['planner'].cursor() as cursor:
        query = f'''SELECT 
        Worker.[worker_id], Worker.[worker], COALESCE(SUM(Task.[duration])/720000.0, 0) AS KPI
        FROM [planner].[dbo].[worker_list] AS Worker
        LEFT JOIN [planner].[dbo].[task_list] AS Task
            ON Worker.[worker_id] = Task.[worker_id]
            AND Task.[date_time] = '{date.strftime('%Y-%m-%d %H:%M:%S')}'
        WHERE Worker.[holidays] != '{date.strftime('%Y-%m-%d %H:%M:%S')}'
        AND Worker.[fired] = 'False'
        GROUP BY Worker.[worker_id], Worker.[worker]'''
        cursor.execute(query)
        kpi_list = cursor.fetchall()
        kpi_asc_list = sorted(kpi_list, key=lambda x: x[2])
        print('kpi_asc_list', kpi_asc_list)
    return min(kpi_list, key=lambda x: x[2])

def insert_film(program_id, worker_id, worker, duration, date, status):
    with connections['planner'].cursor() as cursor:
        columns = '[program_id], [worker_id], [worker], [duration], [date_time], [task_status]'
        query = f'''INSERT INTO [planner].[dbo].[task_list] ({columns})
        VALUES ({program_id}, {worker_id}, '{worker}', {duration}, '{date.strftime('%Y-%m-%d %H:%M:%S')}', '{status}')
        '''
        cursor.execute(query)
        print('successfully added')

def distribution(program_id, program_type_id, duration):
    date = datetime.now()
    planner_worker_list, oplan3_worker_list = cenz_worker(program_id)
    if planner_worker_list:
        planner_worker_id, planner_worker = planner_worker_list
    else:
        planner_worker_id, planner_worker = None, None
    if oplan3_worker_list:
        int_value, items_string = oplan3_worker_list
        oplan3_worker_id = int_value
        oplan3_worker = items_string.split('\r\n')[int_value]
        print('oplan3_worker: ', oplan3_worker)
    else:
        oplan3_worker_id, oplan3_worker = None, None

    if program_type_id in (4, 5, 6, 10, 11, 12) and not oplan3_worker:
        if not planner_worker:
            status = 'not_ready'
            kpi_info = kpi_min(date)
            if kpi_info[2] < 1:
                worker_id, worker, kpi = kpi_info
                insert_film(program_id, worker_id, worker, duration, date, status)
            else:
                date += timedelta(days=1)
                worker_id, worker, kpi = kpi_min(date)
                insert_film(program_id, worker_id, worker, duration, date, status)
            print('\tdate', date)
        else:
            worker_id = planner_worker_id
            worker = planner_worker
            status = 'not_ready'
    else:
        worker_id = oplan3_worker_id
        worker = oplan3_worker
        status = 'ready'
    return worker_id, worker, status

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
        print('temp_dict', temp_dict)
        program_type_id = temp_dict['Progs_program_type_id']
        duration = temp_dict['Progs_duration']
        worker_id, worker, status = distribution(program_id, program_type_id, duration)
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
                                 'Progs_duration': duration,
                                 'Sched_schedule_name': temp_dict['Sched_schedule_name'],
                                 'SchedDay_day_date': temp_dict['SchedDay_day_date'],
                                 'status': status,
                                 'worker_id': worker_id,
                                 'worker': worker}]}
                program_id_list.append(program_id)
                material_list.append(program_info_dict)
            else:
                material_list[repeat_index]['episode'].append(
                    {'Progs_program_id': temp_dict['Progs_program_id'],
                    'Progs_name': temp_dict['Progs_name'],
                    'Progs_episode_num': temp_dict['Progs_episode_num'],
                    'Progs_duration': duration,
                    'Sched_schedule_name': temp_dict['Sched_schedule_name'],
                    'SchedDay_day_date': temp_dict['SchedDay_day_date'],
                    'status': status,
                    'worker_id': worker_id,
                    'worker': worker})
                program_id_list.append(program_id)
        if not temp_dict['Progs_program_type_id'] in (4, 8, 12):
            program_info_dict = {
                'Progs_program_id': temp_dict['Progs_program_id'],
                'Progs_parent_id': temp_dict['Progs_parent_id'],
                'Progs_name': temp_dict['Progs_name'],
                'Progs_production_year': temp_dict['Progs_production_year'],
                'Progs_duration': duration,
                'Sched_schedule_name': temp_dict['Sched_schedule_name'],
                'SchedDay_day_date': temp_dict['SchedDay_day_date'],
                'type': 'film',
                'status': status,
                'worker_id': worker_id,
                'worker': worker}
            program_id_list.append(program_id)
            material_list.append(program_info_dict)
    return material_list

def oplan_material_list():
    with connections['oplan3'].cursor() as cursor:
        dates = ('2025-03-25', '2025-03-26', '2025-03-27', '2025-03-28', '2025-03-29', '2025-03-30')
        channels = ('Кино +', 'Романтичный сериал', 'Крепкое')
        order = 'ASC'

        columns = [('Progs', 'program_id'), ('Progs', 'parent_id'), ('Progs', 'program_type_id'), ('Progs', 'name'),
                   ('Progs', 'production_year'), ('Progs', 'AnonsCaption'), ('Progs', 'episode_num'),
                   ('Progs', 'duration'), ('Sched', 'schedule_name'), ('SchedDay', 'day_date')]
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
                   ('Files', 'CreationTime'), ('Files', 'ModificationTime'), ('TaskInf', 'worker_id'), ('TaskInf', 'worker')]

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
        full_info_dict['custom_fields'] = cenz_info(program_id)
        full_info_dict['schedule_info'] = schedule_info(program_id)
        return full_info_dict

def cenz_worker(program_id):
    with connections['planner'].cursor() as cursor:
        query_planner = f'''SELECT worker_id, worker
        FROM [planner].[dbo].[task_list]
        WHERE [program_id] = {program_id}'''
        cursor.execute(query_planner)
        planner_worker_list = cursor.fetchone()
    with connections['oplan3'].cursor() as cursor:
        columns = 'Val.[IntValue], Fields.[ItemsString]'
        query_oplan3 = f'''
            SELECT {columns}
            FROM [oplan3].[dbo].[ProgramCustomFields] AS Fields
            JOIN [oplan3].[dbo].[ProgramCustomFieldValues] AS Val
                ON Fields.[CustomFieldID] = Val.[ProgramCustomFieldId]
            WHERE Val.[ObjectId] = {program_id}
            AND Val.[ProgramCustomFieldId] = 15
                '''
        cursor.execute(query_oplan3)
        oplan3_worker_list = cursor.fetchone()
    return planner_worker_list, oplan3_worker_list

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