from django.shortcuts import render
from django.db import connections

def program_id():
    with connections['oplan3'].cursor() as cursor:
        schedule_name = 'Кино +'
        day_date = '2024-02-14'

        query = f'''
        SELECT [program_id]
        FROM [oplan3].[dbo].[scheduled_program]
        WHERE [program_id] > 0
        AND [schedule_day_id] IN
            (SELECT [schedule_day_id]
            FROM [oplan3].[dbo].[schedule_day]
            WHERE [day_date] = '{day_date}'
            AND [schedule_id] IN
                (SELECT [schedule_id]
                FROM [oplan3].[dbo].[schedule]
                WHERE [schedule_name] = '{schedule_name}'))
        '''
        cursor.execute(query)
        program_id_list = [schedule_id[0] for schedule_id in cursor.fetchall()]
        material_list = []

        for program_id in program_id_list:

            field_val_columns = '[ProgramCustomFieldValuesID], [ProgramCustomFieldId], [ObjectId], [TextValue], [IntValue], [DateValue], [ObjectType], [TimeStamp]'
            fields_name_columns = '[CustomFieldID], [Name], [FieldType], [ItemsString], [Position], [ObjectType], [TimeStamp]'

            file_columns = 'Name, Size, CreationTime, ModificationTime'
            program_columns = ('[program_id], [parent_id], [name], [orig_name], [annotation], [duration], [comment], '
                               '[keywords], [anounce_text], [program_type_id], [episode_num], [last_edit_user_id], '
                               '[last_edit_time], [authors], [producer], [production_year], [production_country], [subject], '
                               '[SourceID], [AnonsCaption], [DisplayMediumName], [SourceFileMedium], [EpisodesTotal], '
                               '[MaterialState], [SourceMedium], [HasSourceClip], [AnonsCaptionInherit], [AdultTypeID], '
                               '[CreationDate], [Subtitled], [Season], [Director], [Cast], [MusicComposer], [ShortAnnotation]')
            types_columns = '[type_name]'
            sql_columns = ', '.join(
                [f'Files.{col}' for col in file_columns.split(', ')] +
                [f'Types.{col}' for col in types_columns.split(', ')] +
                [f'Progs.{col}' for col in program_columns.split(', ')])
            django_columns = ', '.join(
                [f'Files_{col}' for col in file_columns.split(', ')] +
                [f'Types_{col}' for col in types_columns.split(', ')] +
                [f'Progs_{col}' for col in program_columns.split(', ')])
            # ', '.join([f'Val.{col}' for col in field_val_columns.split(', ')])+", "+
            # ', '.join(f'Fields.{col}' for col in fields_name_columns.split(', '))+", "+
            query = f'''
            SELECT {sql_columns}
            FROM [oplan3].[dbo].[File] AS Files
            JOIN [oplan3].[dbo].[Clip] AS Clips
                ON Files.[ClipID] = Clips.[ClipID]
            JOIN [oplan3].[dbo].[program] AS Progs
                ON Clips.[MaterialID] = Progs.[SuitableMaterialForScheduleID]
            JOIN [oplan3].[dbo].[program_type] AS Types
                ON Progs.[program_type_id] = Types.[program_type_id]
            WHERE Files.[Deleted] = 0
            AND Files.[PhysicallyDeleted] = 0
            AND Clips.[Deleted] = 0
            AND Progs.[deleted] = 0
            AND Progs.[program_id] = '{program_id}'
            AND Progs.[program_type_id] NOT IN (3, 9, 13, 14, 15, 17, 18)
                    '''
            cursor.execute(query)
            full_info = cursor.fetchone()
            if full_info:
                full_info_dict = dict(zip(django_columns.split(', '), full_info))
                material_list.append(full_info_dict)
                print(full_info_dict)
    return material_list

def day(request):
    return render(request, 'main/day.html')

def week(request):
    return render(request, 'main/week.html')

def month(request):
    return render(request, 'main/month.html')

def full_list(request):
    main_search = request.GET.get('search', None)
    channels = request.POST.get('channel_filter', None)
    workers = request.POST.get('worker_filter', None)
    if channels:
        print(channels)
    if workers:
        print(workers)
    if main_search:
        print(main_search)
    data = {'material_list':
                [
                    {'id': 1398, 'type': 'film', 'name': 'Служебный роман', 'year': 1990, 'channel': 'Крепкое', 'air_date': '15.02.2025', 'worker': 'Александр Кисляков'},
                    {'id': 1399, 'type': 'film', 'name': 'Avengers', 'year': 2019, 'channel': 'Кино +', 'air_date': '14.02.2025', 'worker': 'Ольга Кузовкина'},
                    {'id': 1398, 'type': 'film', 'name': 'Служебный роман', 'year': 1990, 'channel': 'Крепкое', 'air_date': '15.02.2025', 'worker': 'Александр Кисляков'},
                    {'id': 1399, 'type': 'film', 'name': 'Avengers', 'year': 2019, 'channel': 'Кино +', 'air_date': '14.02.2025', 'worker': 'Ольга Кузовкина'},
                    {'id': 1498, 'type': 'series', 'name': 'Avengers_S01', 'year': 2025, 'episode':
                        [{'id': 145, 'name': 'Avengers_S01E01', 'channel': 'Наше детство', 'air_date': '25.02.2025', 'worker': 'Айнур Мингазов'},
                         {'id': 147, 'name': 'Avengers_S01E02', 'channel': 'Наше детство', 'air_date': '25.02.2025', 'worker': 'Ольга Кузовкина'},
                         {'id': 148, 'name': 'Avengers_S01E03', 'channel': 'Наше детство', 'air_date': '25.02.2025', 'worker': 'Айнур Мингазов'}]},
                    {'id': 1398, 'type': 'film', 'name': 'Служебный роман', 'year': 1990, 'channel': 'Крепкое', 'air_date': '15.02.2025', 'worker': 'Александр Кисляков'},
                    {'id': 1498, 'type': 'series', 'name': 'Avengers_S01', 'year': 2025, 'episode':
                        [{'id': 145, 'name': 'Avengers_S02E01', 'channel': 'Наше детство', 'air_date': '02.03.2025', 'worker': 'Айнур Мингазов'},
                         {'id': 147, 'name': 'Avengers_S02E02', 'channel': 'Наше детство', 'air_date': '03.03.2025', 'worker': 'Ольга Кузовкина'},]}
                ]
            }
    data = {'material_list': program_id}
    return render(request, 'main/list.html', data)

