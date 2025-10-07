import ast
import json
from datetime import datetime, date

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.forms import model_to_dict
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.contrib import messages

from main.logs_and_history import get_task_status, change_task_status_final, insert_history_status, update_comment
from main.permission_pannel import ask_db_permissions
from messenger_static.messenger_utils import create_notification
from .forms import TaskSearchForm, OnAirReportFilter, OnAirCalendar
from .models import OnAirModel, TaskSearch
from .on_air_calendar import calendar_skeleton, calc_next_month, calc_prev_month, update_info
from .on_air_task_list import task_info
from .report import prepare_service_dict, task_list_for_channel


def report(request):
    today = date.today()
    cal_year = today.year
    cal_month = today.month
    return redirect(month_report, cal_year=cal_year, cal_month=cal_month)

@login_required()
def month_report(request):
    worker_id = request.user.id

    current_date = datetime.now()

    # Получаем параметры из GET-запроса или используем значения по умолчанию
    cal_year = request.GET.get('year', current_date.year)
    cal_month = request.GET.get('month', current_date.month)
    channel = request.GET.get('channel', '')

    summary_table = [
        ('no_material', 'Материал отсутствует'),
        ('not_ready', 'Не готов'),
        ('fix', 'Исправление исходника'),
        ('fix_ready', 'Исходник исправлен'),
        ('ready', 'Отсмотрен'),
        ('otk', 'Прошёл ОТК'),
        ('otk_fail', 'Не прошёл ОТК'),
        ('final', 'Готов к эфиру'),
        ('final_fail', 'Не прошёл ЭК'),
        ('ready_oplan3', 'Завершено в Oplan3'),
    ]

    if request.method == 'POST':
        calendar_form = OnAirCalendar(request.POST)
        if calendar_form.is_valid():
            cal_year = int(calendar_form.cleaned_data['year_dropdown'])
            cal_month = int(calendar_form.cleaned_data['month_dropdown'])
            channel = calendar_form.cleaned_data.get('channel_dropdown')
        else:
            print('form is not valid', calendar_form.errors)
    else:
        calendar_form = OnAirCalendar(initial={'year_dropdown': cal_year, 'month_dropdown': cal_month})

    data = {
        'on_air_calendar': calendar_skeleton(cal_year, cal_month),
        'calendar_form': calendar_form,
        'summary_table': summary_table,
        'permissions': ask_db_permissions(worker_id),
    }
    return render(request, 'on_air_report/on_air_calendar.html', data)

def load_on_air_calendar_info(request):
    date_str = request.GET.get('date')
    schedule_id = request.GET.get('schedule_id', '')
    try:
        current_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid date'}, status=400)
    try:
        return JsonResponse(update_info(current_date, schedule_id))
    except Exception as error:
        return JsonResponse({'error': str(error)}, status=500)

@login_required()
def today_report(request):
    today = datetime.today()
    return redirect(date_report, cal_year=today.year, cal_month=today.month, cal_day=today.day)

@login_required()
def date_report(request, cal_year, cal_month, cal_day, schedule_id=None):
    user_id = request.user.id
    cal_date = date(cal_year, cal_month, cal_day)
    if schedule_id:
        schedule_id_list = (schedule_id,)
    else:
        schedule_id_list = (3, 5, 6, 7, 8, 9, 10, 11, 12, 20)
    data = {
        'schedule_id_list': schedule_id_list,
        'service_dict': prepare_service_dict(cal_year, cal_month, cal_day, cal_date),
        'permissions': ask_db_permissions(user_id)
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

@login_required()
def on_air_search(request):
    user_id = request.user.id

    try:
        on_air_inst_dict = OnAirModel.objects.get(owner=user_id)
    except ObjectDoesNotExist:
        default_filter = OnAirModel(owner=user_id)
        default_filter.save()
        on_air_inst_dict = OnAirModel.objects.get(owner=user_id)
        print("Новый OnAirModel фильтр создан")

    try:
        search_inst_dict = TaskSearch.objects.get(owner=user_id)
    except ObjectDoesNotExist:
        default_search = TaskSearch(owner=user_id, search_type=1, sql_set=100)
        default_search.save()
        search_inst_dict = TaskSearch.objects.get(owner=user_id)

    if request.method == 'POST':
        search_filter = TaskSearchForm(request.POST, instance=search_inst_dict)
        if search_filter.is_valid():
            search_filter.save()
        on_air_filter = OnAirReportFilter(request.POST, instance=on_air_inst_dict)
        if on_air_filter.is_valid():
            on_air_filter.save()
    else:
        # on_air_init_dict = {
        #     'schedules': evaluate(on_air_inst_dict.schedules),
        #     'workers': evaluate(on_air_inst_dict.workers),
        #     'material_type': evaluate(on_air_inst_dict.material_type),
        #     'work_dates': on_air_inst_dict.ready_dates,
        #     'sched_dates': on_air_inst_dict.sched_dates,
        #     'task_status': evaluate(on_air_inst_dict.task_status)
        # }
        on_air_init_dict = serialize(model_to_dict(on_air_inst_dict))
        on_air_filter = OnAirReportFilter(initial=on_air_init_dict)
        search_filter = TaskSearchForm(initial={'sql_set': search_inst_dict.sql_set, 'search_type': search_inst_dict.search_type})
    data = {
        'on_air_filter': on_air_filter,
        'search_filter': search_filter,
        'permissions': ask_db_permissions(user_id),
    }
    return render(request, 'on_air_report/on_air_search.html', data)

def load_on_air_task_table(request):
    search_input = request.GET.get('search_input', '')
    user_id = request.user.id
    queryset = OnAirModel.objects.get(owner=user_id)
    field_dict = {}
    if queryset:
        field_dict = serialize(model_to_dict(queryset))

    print(field_dict)
    search_inst_dict = TaskSearch.objects.get(owner=user_id)

    task_list = task_info(field_dict, search_inst_dict.search_type, search_input, search_inst_dict.sql_set)

    html = render_to_string(
        'on_air_report/on_air_task_table.html',
        {
            'task_list': task_list,
            'permissions': ask_db_permissions(user_id),
        },
        request=request
    )
    return JsonResponse({'html': html})

def evaluate(value):
    try:
        return ast.literal_eval(value)
    except Exception as error:
        print(error)
        return value

def serialize(on_air_instance):
    field_dict = {}
    for key, value in on_air_instance.items():
        try:
            if key in ('owner', 'ready_dates', 'sched_dates'):
                field_dict[key] = value
            else:
                field_dict[key] = ast.literal_eval(value)
        except Exception as error:
            print(error)
            field_dict[key] = []
    return field_dict

def apply_final_batch(request):
    success_messages = []
    error_messages = []

    worker_id = request.user.id
    try:
        approve_list_list = json.loads(request.body)

        if not approve_list_list:
            return JsonResponse({'status': 'error', 'message': 'Нет изменений'})

        for program_id in approve_list_list:
            db_task_status = get_task_status(program_id)
            if db_task_status in ('no_material', 'not_ready', 'fix', 'otk_fail', 'final_fail'):
                return JsonResponse(
                    {'status': 'error', 'message': f'Ошибка! Изменения не были внесены. Недостаточно прав доступа.'})
            answer = change_task_status_final(program_id, 'final', db_task_status)
            if answer.get('status') == 'success':
                insert_history_status(program_id, worker_id, db_task_status, 'final')
                success_messages.append(answer.get('message'))
            else:
                error_messages.append(answer.get('message'))

        if success_messages:
            messages.success(request, '\n'.join(success_messages))
        if error_messages:
            messages.error(request, '\n'.join(error_messages))
        return JsonResponse({'status': 'success', 'message': 'message'})
    except Exception as error:
        print(error)
        return JsonResponse({'error': str(error)}, status=500)


def final_fail_batch(request):
    success_messages = []
    error_messages = []

    user_id = request.user.id
    try:
        program_list = json.loads(request.body)

        if not program_list:
            return JsonResponse({'status': 'error', 'message': 'Нет изменений'})

        for material in program_list:
            program_id= material.get('program_id')
            recipient = material.get('recipient')
            comment = material.get('comment')
            deadline = material.get('deadline')

            if recipient == 'otk':
                recipient = 6

            db_task_status = get_task_status(program_id)
            if db_task_status in ('no_material', 'not_ready', 'fix', 'otk_fail', 'final_fail'):
                return JsonResponse(
                    {'status': 'error', 'message': f'Ошибка! Изменения не были внесены. Недостаточно прав доступа.'})
            answer = change_task_status_final(program_id, 'final_fail', db_task_status)
            if answer.get('status') == 'success':
                insert_history_status(program_id, user_id, db_task_status, 'final_fail')
                if comment:
                    update_comment(program_id, user_id, task_status='final_fail', comment=comment, deadline=deadline)
                notification_data = {
                    'sender': user_id, 'recipient': recipient, 'program_id': program_id,
                    'message': comment, 'comment': 'Материал не прошёл эфирный контроль'
                }
                create_notification(notification_data)
                success_messages.append(answer.get('message'))
            else:
                error_messages.append(answer.get('message'))

        if success_messages:
            messages.success(request, '\n'.join(success_messages))
        if error_messages:
            messages.error(request, '\n'.join(error_messages))
        return JsonResponse({'status': 'success', 'message': 'message'})
    except Exception as error:
        print(error)
        return JsonResponse({'error': str(error)}, status=500)
