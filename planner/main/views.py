from django.shortcuts import render
from .list_view import list_material_list
from .week_view import week_material_list
from .kpi_admin_panel import kpi_info_dict
from .ffmpeg_info import ffmpeg_dict
from .detail_view import full_info


def index(request):
    return render(request, 'main/index.html')

def day(request):
    return render(request, 'main/day.html')

def week(request):
    data = {'week_material_list': week_material_list,
            }
    return render(request, 'main/week.html', data)

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
        print('main:', main_search)

    data = {'material_list': list_material_list,
            }
    return render(request, 'main/list.html', data)

def material_card(request, program_id):
    data = {'full_info': full_info(program_id),
            'ffmpeg': ffmpeg_dict(program_id),
            }
    return render(request, 'main/full_info_card.html', data)

def kpi_info(request):
    work_date = request.POST.get('work_date',  '2025-03-01')
    workers = request.POST.get('workers', (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11))
    data = kpi_info_dict(work_date, workers)
    return render(request, 'main/kpi_admin_panel.html', data)

def kpi_worker(request, worker_id):
    work_date = request.POST.get('work_date', '2025-03-01')
    # worker = (5, 5)
    data = kpi_info_dict(work_date, worker_id)
    return render(request, 'main/kpi_worker.html', data)