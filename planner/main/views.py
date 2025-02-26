from django.shortcuts import render
from .sql_connection import oplan_material_list, full_info
from .ffprobe_scan import ffmpeg_scan
from .kpi_admin_panel import kpi_info_dict


def day(request):
    return render(request, 'main/day.html')

def week(request):
    data = {'material_list': oplan_material_list,
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

    data = {'material_list': oplan_material_list,
            }
    return render(request, 'main/list.html', data)


def material_card(request, id_card):
    data = {'full_info': full_info(id_card),
            'ffmpeg': ffmpeg_scan(r"E:\TEST_Material\F_From Dusk Till Dawn 2 Texas Blood Money_1998.mp4")}
    return render(request, 'main/full_info_card.html', data)

def kpi_info(request):
    work_date = request.POST.get('work_date',  '2025-02-26')
    if work_date:
        print(work_date)
    data = {'task_list': kpi_info_dict(work_date)}
    return render(request, 'main/kpi_admin_panel.html', data)