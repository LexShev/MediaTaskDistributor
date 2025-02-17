from django.shortcuts import render
from .sql_connection import oplan_material_list, full_info, cenz_info


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
        # program_id(channels)
    if workers:
        print(workers)
    if main_search:
        print('main:', main_search)
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
    data = {'material_list': oplan_material_list,
            'full_info': full_info}
    return render(request, 'main/list.html', data)


