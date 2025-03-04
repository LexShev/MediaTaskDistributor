import datetime

from django.shortcuts import render, redirect
from .list_view import list_material_list
from .week_view import week_material_list
from .kpi_admin_panel import kpi_summary_calc, kpi_personal_calc
from .ffmpeg_info import ffmpeg_dict
from .detail_view import full_info
from .distribution import main_distribution


def index(request):
    return render(request, 'main/index.html')

def day(request):
    return render(request, 'main/day.html')

def week(request):
    # start_day = datetime.datetime.today() - datetime.timedelta(days=datetime.datetime.today().weekday())
    start_day = datetime.datetime.today()
    start_day.strftime('%Y/%U')
    # data = week_material_list(start_day)
    # return render(request, 'main/week.html', data)
    return redirect(week_date, start_day.year, start_day.isocalendar().week)

def week_date(request, work_year, work_week):
    data = week_material_list(work_year, work_week)
    return render(request, 'main/week.html', data)

def month(request):
    return render(request, 'main/month.html')

def full_list(request):
    main_search = request.GET.get('search', None)
    channels = request.POST.get('channel_filter', None)
    workers = request.POST.get('worker_filter', None)
    dates = request.POST.get('dates_filter', ('2025-03-07', '2025-03-02', '2025-03-03', '2025-03-04', '2025-03-05'))
    data = {'material_list': list_material_list(dates),
            }
    main_distribution()
    return render(request, 'main/list.html', data)

def material_card(request, program_id):
    data = {'full_info': full_info(program_id),
            'ffmpeg': ffmpeg_dict(program_id),
            }
    return render(request, 'main/full_info_card.html', data)

def kpi_info(request):
    work_date = request.POST.get('work_date', str(datetime.datetime.today().date()))
    workers = request.POST.get('workers', (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11))
    data = kpi_summary_calc(work_date, workers)
    return render(request, 'main/kpi_admin_panel.html', data)

def kpi_worker(request, worker_id):
    work_date = request.POST.get('work_date', str(datetime.datetime.today().date()))
    data = kpi_personal_calc(work_date, worker_id)
    return render(request, 'main/kpi_worker.html', data)