from django.shortcuts import render
from django.db import connections

def program_id():
    with connections['oplan3'].cursor() as cursor:
        dates = ('2024-02-16', '2024-02-17')
        channels = ('Крепкое', 'Крепкое')
        order = 'ASC'
        material_list = []

        field_val_columns = '[ProgramCustomFieldValuesID], [ProgramCustomFieldId], [ObjectId], [TextValue], [IntValue], [DateValue], [ObjectType], [TimeStamp]'
        fields_name_columns = '[CustomFieldID], [Name], [FieldType], [ItemsString], [Position], [ObjectType], [TimeStamp]'

        file_columns = ('Name', 'Size', 'CreationTime', 'ModificationTime')
        program_columns = ('program_id', 'parent_id', 'name', 'orig_name', 'annotation', 'duration', 'comment',
                           'keywords', 'anounce_text', 'program_type_id', 'episode_num', 'last_edit_user_id',
                           'last_edit_time', 'authors', 'producer', 'production_year', 'production_country',
                           'subject', 'SourceID', 'AnonsCaption', 'DisplayMediumName', 'SourceFileMedium',
                           'EpisodesTotal', 'MaterialState', 'SourceMedium', 'HasSourceClip', 'AnonsCaptionInherit',
                           'AdultTypeID', 'CreationDate', 'Subtitled', 'Season', 'Director', 'Cast',
                           'MusicComposer', 'ShortAnnotation')

        sql_columns = ', '.join(
            [f'Files.[{col}]' for col in file_columns] + [f'Progs.[{col}]' for col in program_columns] + [
                'Types.[type_name]', 'SchedDay.[day_date]', 'Sched.[schedule_name]'])
        django_columns = [f'Files_{col}' for col in file_columns] + [f'Progs_{col}' for col in program_columns] + [
            'Types_type_name', 'SchedDay_day_date', 'Sched_schedule_name']
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
        material_list = [dict(zip(django_columns, values)) for values in cursor.fetchall()]
        for mat in material_list:
            print(mat)
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

