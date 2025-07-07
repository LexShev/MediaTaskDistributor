from datetime import datetime, date

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from main.permission_pannel import ask_db_permissions
from .report import report_calendar, collect_channels_list, prepare_service_dict


def report(request):
    today = datetime.today()
    cal_year, cal_month = today.year, today.month
    return redirect(report_date, cal_year, cal_month)

@login_required()
def report_date(request, cal_year, cal_month):
    worker_id = request.user.id

    cal_day = request.POST.get('cal_day', date(cal_year, cal_month, day=1))
    if isinstance(cal_day, str):
        cal_day = datetime.strptime(cal_day, '%Y-%m-%d')
    month_calendar = report_calendar(cal_year, cal_month)
    channels_list = collect_channels_list(cal_day)
    data = {'month_calendar': month_calendar,
            'channels_list': channels_list,
            'service_dict': prepare_service_dict(cal_year, cal_month, cal_day),
            'permissions': ask_db_permissions(worker_id)}
    return render(request, 'on_air_report/on_air_report.html', data)