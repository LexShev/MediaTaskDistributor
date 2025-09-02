from datetime import datetime, date

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string

from main.permission_pannel import ask_db_permissions
from .on_air_calendar import calendar_skeleton, calc_next_month, calc_prev_month, update_info
from .report import collect_channels_list, prepare_service_dict, task_list_for_channel


def report(request):
    today = date.today()
    cal_year = today.year
    cal_month = today.month
    return redirect(month_report, cal_year=cal_year, cal_month=cal_month)

@login_required()
def month_report(request, cal_year, cal_month):
    worker_id = request.user.id

    prev_year, prev_month = calc_prev_month(cal_year, cal_month)
    next_year, next_month = calc_next_month(cal_year, cal_month)
    service_dict = {
        'cal_year': cal_year,
        'cal_month': cal_month,
        'prev_year': prev_year,
        'prev_month': prev_month,
        'next_year': next_year,
        'next_month': next_month,
    }
    summary_table = [
        ('no_material', 'Материал отсутствует'),
        ('not_ready', 'Не готов'),
        ('fix', 'Исправление исходника'),
        ('fix_ready', 'Исходник исправлен'),
        ('ready', 'Отсмотрен'),
        ('otk', 'Прошёл ОТК'),
        ('otk_fail', 'На доработке'),
        ('final', 'Готов к эфиру'),
        ('ready_fail', 'На пересмотр'),
        ('ready_oplan3', 'Завершено в Oplan3')
    ]
    data = {
        'on_air_calendar': calendar_skeleton(cal_year, cal_month),
        'service_dict': service_dict,
        'summary_table': summary_table,
        'permissions': ask_db_permissions(worker_id),
    }
    return render(request, 'on_air_report/on_air_calendar.html', data)

def load_on_air_calendar_info(request):
    date_str = request.GET.get('date')
    try:
        current_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid date'}, status=400)
    return JsonResponse(update_info(current_date))

@login_required()
def report_date(request, cal_year, cal_month, cal_day):
    worker_id = request.user.id
    cal_date = date(cal_year, cal_month, cal_day)
    # if isinstance(cal_day, str):
    #     cal_day = datetime.strptime(cal_day, '%Y-%m-%d')
    # month_calendar = report_calendar(cal_year, cal_month)
    schedule_id_list = (3, 5, 6, 7, 8, 9, 10, 11, 12, 20)
    data = {
        'schedule_id_list': schedule_id_list,
        'service_dict': prepare_service_dict(cal_year, cal_month, cal_day, cal_date),
        'permissions': ask_db_permissions(worker_id)
    }
    return render(request, 'on_air_report/on_air_report.html', data)

def get_schedule_table(request, sched_date, schedule_id):
    worker_id = request.user.id
    try:
        html = render_to_string(
            'on_air_report/schedule_table.html',
            {
                'task_list': task_list_for_channel(sched_date, schedule_id),
                # 'service_dict': prepare_service_dict(cal_year, cal_month, cal_day),
                'permissions': ask_db_permissions(worker_id),
            },
            request=request
        )
        return JsonResponse({'html': html})
    except Exception as e:
        print(e)
        return JsonResponse({'error': str(e)}, status=500)