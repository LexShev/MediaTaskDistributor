from datetime import date, datetime

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render

from messenger_static.models import Message, Notification
from home.home_calendar import calendar_skeleton, update_info
from home.home_kpi import common_kpi, daily_kpi
from home.home_table import home_common_table
from main.permission_pannel import ask_db_permissions


@login_required()
def home(request):
    worker_id = request.user.id
    today = date.today()
    service_dict = {
        'today': today,
        'cal_month': today.month,
    }
    data = {
        'home_calendar': calendar_skeleton(),
        'home_table': home_common_table(),
        'service_dict': service_dict,
        'permissions': ask_db_permissions(worker_id),
    }
    return render(request, 'home/home.html', data)

def load_daily_kpi_chart(request):
    return JsonResponse(daily_kpi())

def load_kpi_chart(request):
    return JsonResponse(common_kpi())

def update_total_unread_count(request):
    worker_id = request.user.id
    try:
        total_unread_count = Message.objects.exclude(views__worker_id=worker_id).count()
        unread_notifications = Notification.objects.filter(recipient=worker_id, is_read=False).count()
        return JsonResponse({
            'status': 'success',
            'message': 'Updated successfully',
            'total_unread': total_unread_count + unread_notifications,
        })
    except Exception as e:
        print(e)
        return JsonResponse({'status': 'error', 'message': str(e)}, status=405)

def load_calendar_info(request):
    date_str = request.GET.get('date')
    try:
        current_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid date'}, status=400)
    try:
        calendar_info = update_info(current_date)
        return JsonResponse(calendar_info)
    except Exception as error:
        return JsonResponse({'status': 'error', 'message': str(error)}, status=500)
