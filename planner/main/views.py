import json
from datetime import datetime
import ast

from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.template.loader import render_to_string

from messenger_static.messenger_utils import create_notification
from tools.tasks import process_video_task

from .ffmpeg_info import ffmpeg_dict
from tools.ffprobe_scan import FfprobeScanner
from .forms import ListFilter, WeekFilter, CenzFormText, CenzFormDropDown, KpiForm, VacationForm, AttachedFilesForm, \
    SortingForm

from main.helpers import get_engineer_id
from .js_requests import program_name
from .kinoroom_parser import download_poster, search, check_db
from .logs_and_history import insert_history, select_actions, update_comment, insert_history_new, \
    change_task_status_new, get_task_status
from .models import ModelFilter, AttachedFiles, ModelSorting
from .list_view import list_material_list
from .object_block import unblock_object_planner, block_object_planner, check_planner_lock, \
    check_oplan3_lock
from .permission_pannel import ask_db_permissions
from .templatetags.custom_filters import planner_worker_name
from .week_view import week_material_list
from .kpi_admin_panel import kpi_summary_calc, kpi_personal_calc
from .detail_view import full_info, cenz_info, schedule_info, calc_otk_deadline, \
    comments_history, select_filepath_history, change_oplan_cenz_info
from .work_calendar import my_work_calendar, drop_day_off, insert_day_off, vacation_info, insert_vacation, drop_vacation


def handle_error(request, status_code, exception=None):
    # Словарь с описаниями ошибок
    error_messages = {
        400: "Неверный запрос (Bad Request)",
        403: "Доступ запрещён (Forbidden)",
        404: "Страница не найдена (Not Found)",
        500: "Ошибка сервера (Server Error)",
    }

    context = {
        'error_code': status_code,
        'error_message': error_messages.get(status_code, "Неизвестная ошибка"),
        'exception': str(exception) if exception else None,
    }

    return render(request, 'main/errors.html', context, status=status_code)

from django.shortcuts import render

def bad_request(request, exception):
    return render(request, 'main/errors.html', status=400)

def permission_denied(request, exception):
    return render(request, 'main/errors.html', status=403)

def page_not_found(request, exception):
    return render(request, 'main/errors.html', status=404)

def server_error(request):
    return render(request, 'main/errors.html', status=500)

def day(request):
    return render(request, 'main/day.html')

def week(request):
    start_day = datetime.today()
    start_day.strftime('%Y/%U')
    return redirect(week_date, start_day.year, start_day.isocalendar().week)

@login_required()
def week_date(request, work_year, work_week):
    user_id = request.user.id
    try:
        inst_dict = ModelFilter.objects.get(owner=user_id)
    except ObjectDoesNotExist:
        schedules = (1, 3, 5, 6, 7, 8, 9, 10, 11, 12, 20)
        start_date = datetime.today()
        work_dates = (start_date, start_date)
        task_status = ('not_ready', 'ready', 'fix')
        material_type = ('film', 'season')

        default_filter = ModelFilter(
            owner=user_id, schedules=schedules,
            workers=[user_id], material_type=material_type,
            work_dates=' - '.join([work_date.strftime('%d.%m.%Y') for work_date in work_dates]),
            task_status=task_status
        )
        default_filter.save()
        inst_dict = ModelFilter.objects.get(owner=user_id)
        print("Новый фильтр создан")

    try:
        sorting_inst_dict = ModelSorting.objects.get(owner=user_id)
    except ObjectDoesNotExist:
        default_sorting = ModelSorting(owner=user_id, user_order='sched_date', order_type='ASC')
        default_sorting.save()
        sorting_inst_dict = ModelSorting.objects.get(owner=user_id)
        print("Новая сортировка создана")

    if request.method == 'POST':
        filter_form = WeekFilter(request.POST, instance=inst_dict)
        sorting_form = SortingForm(request.POST, instance=sorting_inst_dict)
        if filter_form.is_valid() and sorting_form.is_valid():
            filter_form.save()
            sorting_form.save()

            schedules = ast.literal_eval(filter_form.cleaned_data.get('schedules'))
            workers = ast.literal_eval(filter_form.cleaned_data.get('workers'))
            material_type = ast.literal_eval(filter_form.cleaned_data.get('material_type'))
            task_status = ast.literal_eval(filter_form.cleaned_data.get('task_status'))

            user_order = sorting_form.cleaned_data.get('user_order')
            order_type = sorting_form.cleaned_data.get('order_type')

        else:
            schedules = (3, 5, 6, 7, 8, 9, 10, 11, 12, 20)
            workers = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)
            task_status = ('not_ready', 'ready', 'fix')
            material_type = ('film', 'season')

            user_order = 'sched_date'
            order_type = 'ASC'
    else:
        schedules = ast.literal_eval(inst_dict.schedules)
        workers = ast.literal_eval(inst_dict.workers)
        material_type = ast.literal_eval(inst_dict.material_type)
        task_status = ast.literal_eval(inst_dict.task_status)

        user_order = sorting_inst_dict.user_order
        order_type = sorting_inst_dict.order_type

        initial_dict = {'schedules': schedules,
                        'workers': workers,
                        'material_type': material_type,
                        'task_status': task_status}
        filter_form = WeekFilter(initial=initial_dict)
        sorting_form = SortingForm(initial={'user_order': user_order, 'order_type': order_type})
    material_list, service_dict = week_material_list(schedules, workers, material_type, task_status, work_year, work_week, user_order, order_type)
    data = {
        'week_material_list': material_list,
        'service_dict': service_dict,
        'permissions': ask_db_permissions(user_id),
        'form': filter_form,
        'sorting_form': sorting_form
    }
    return render(request, 'main/week.html', data)


@login_required()
def full_list(request):
    user_id = request.user.id
    try:
        inst_dict = ModelFilter.objects.get(owner=user_id)
    except ObjectDoesNotExist:
        schedules = (1, 3, 5, 6, 7, 8, 9, 10, 11, 12, 20)
        start_date = datetime.today()
        work_dates = (start_date, start_date)
        task_status = ('not_ready', 'ready', 'fix')
        material_type = ('film', 'season')

        default_filter = ModelFilter(
            owner=user_id, schedules=schedules,
            workers=[user_id], material_type=material_type,
            work_dates=' - '.join([work_date.strftime('%d.%m.%Y') for work_date in work_dates]),
            task_status=task_status
        )
        default_filter.save()
        inst_dict = ModelFilter.objects.get(owner=user_id)
        print("Новый фильтр создан")
    try:
        sorting_inst_dict = ModelSorting.objects.get(owner=user_id)
    except ObjectDoesNotExist:
        default_sorting = ModelSorting(owner=user_id, user_order='sched_date', order_type='ASC')
        default_sorting.save()
        sorting_inst_dict = ModelSorting.objects.get(owner=user_id)
        print("Новая сортировка создана")
    if request.method == 'POST':
        filter_form = ListFilter(request.POST, instance=inst_dict)
        sorting_form = SortingForm(request.POST, instance=sorting_inst_dict)
        if filter_form.is_valid() and sorting_form.is_valid():
            filter_form.save()
            sorting_form.save()

            schedules = ast.literal_eval(filter_form.cleaned_data.get('schedules'))
            workers = ast.literal_eval(filter_form.cleaned_data.get('workers'))
            material_type = ast.literal_eval(filter_form.cleaned_data.get('material_type'))
            work_dates = tuple(map(lambda d: datetime.strptime(d, '%d.%m.%Y'), filter_form.cleaned_data.get('work_dates').split(' - ')))
            task_status = ast.literal_eval(filter_form.cleaned_data.get('task_status'))

            user_order = sorting_form.cleaned_data.get('user_order')
            order_type = sorting_form.cleaned_data.get('order_type')

        else:
            schedules = (1, 3, 5, 6, 7, 8, 9, 10, 11, 12, 20)
            start_date = datetime.today()
            work_dates = (start_date, start_date)
            workers = (3, 5, 4, 7, 8, 9, 10, 11, 12, 13)
            task_status = ('not_ready', 'ready', 'fix')
            material_type = ('film', 'season')

            user_order = 'sched_date'
            order_type = 'ASC'
    else:
        schedules = ast.literal_eval(inst_dict.schedules)
        workers = ast.literal_eval(inst_dict.workers)
        material_type = ast.literal_eval(inst_dict.material_type)
        work_dates = tuple(map(lambda d: datetime.strptime(d, '%d.%m.%Y'), inst_dict.work_dates.split(' - ')))
        task_status = ast.literal_eval(inst_dict.task_status)

        user_order = sorting_inst_dict.user_order
        order_type = sorting_inst_dict.order_type

        initial_dict = {'schedules': schedules,
                        'workers': workers,
                        'material_type': material_type,
                        'work_dates': ' - '.join([work_date.strftime('%d.%m.%Y') for work_date in work_dates]),
                        'task_status': task_status}
        filter_form = ListFilter(initial=initial_dict)
        sorting_form = SortingForm(initial={'user_order': user_order, 'order_type': order_type})
    data = {'material_list': list_material_list(schedules, workers, material_type, work_dates, task_status, user_order, order_type),
            'form': filter_form, 'sorting_form': sorting_form, 'permissions': ask_db_permissions(user_id)}
    return render(request, 'main/list.html', data)

def get_field_comparison(program_id_list, fields_to_compare):
    initial_dict = {}
    initial_values = {field: None for field in fields_to_compare}
    has_differences = {field: False for field in fields_to_compare}

    for program_id in program_id_list:
        custom_fields = cenz_info(program_id)

        for field in fields_to_compare:
            current_value = custom_fields.get(field, '')

            if initial_values.get(field) is None:
                initial_values[field] = current_value
            elif not has_differences.get(field) and current_value != initial_values.get(field):
                has_differences[field] = True

    for field_id, field_name in fields_to_compare.items():
        if has_differences.get(field_id):
            if field_id in (17, 7, 14, 15, 18, 19, 22):
                initial_dict[field_name] = '-'
            else:
                initial_dict[field_name] = 'несколько значений'
        else:
            initial_dict[field_name] = initial_values.get(field_id) if initial_values.get(field_id) is not None else ''
    return initial_dict

def load_cenz_data(request):
    try:
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)
        program_id_list = json.loads(request.body)

        if not program_id_list:
            return JsonResponse({'status': 'error', 'message': 'No data provided'}, status=400)

        fields_to_compare = {
            8: 'lgbt_form',
            9: 'sig_form',
            10: 'obnazh_form',
            11: 'narc_form',
            12: 'mat_form',
            13: 'other_form',
            16: 'editor_form',

            17: 'meta_form',
            7: 'work_date_form',
            14: 'cenz_rate_form',
            15: 'engineers_form',
            18: 'tags_form',
            19: 'inoagent_form',
            22: 'narc_select_form',
        }

        initial_dict = get_field_comparison(program_id_list, fields_to_compare)

        html = render_to_string('main/block_cenz.html', {
            'form_drop': CenzFormDropDown(comparison_data=initial_dict),
            'form_text': CenzFormText(comparison_data=initial_dict),
        }, request=request)
        return JsonResponse({'status': 'success', 'message': 'Data loaded successfully', 'html': html})
    except Exception as e:
        print(e)
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

# def submit_cenz_data(request):
#     success_messages = []
#     error_messages = []
#     user_id = request.user.id
#     if request.method == 'POST':
#
#         form_drop = CenzFormDropDown(request.POST)
#         form_text = CenzFormText(request.POST)
#
#         if form_text.is_valid() and form_drop.is_valid():
#             new_values_dict = {
#                 17: form_drop.cleaned_data.get('meta_form'),
#                 7: form_drop.cleaned_data.get('work_date_form'),
#                 14: form_drop.cleaned_data.get('cenz_rate_form'),
#                 15: form_drop.cleaned_data.get('engineers_form'),
#                 18: form_drop.cleaned_data.get('tags_form'),
#                 19: form_drop.cleaned_data.get('inoagent_form'),
#                 22: form_drop.cleaned_data.get('narc_select_form'),
#                 8: form_text.cleaned_data.get('lgbt_form'),
#                 9: form_text.cleaned_data.get('sig_form'),
#                 10: form_text.cleaned_data.get('obnazh_form'),
#                 11: form_text.cleaned_data.get('narc_form'),
#                 12: form_text.cleaned_data.get('mat_form'),
#                 13: form_text.cleaned_data.get('other_form'),
#                 16: form_text.cleaned_data.get('editor_form')
#             }
#         else:
#             new_values_dict = {}
#
#         task_ready_list = []
#         task_status = ''
#         task_ready = request.POST.get('task_ready')
#         cenz_info_change = request.POST.get('cenz_info_change')
#         if task_ready:
#             task_status = 'ready'
#             task_ready_list = task_ready.split(',')
#         if cenz_info_change:
#             task_status = ''
#             task_ready_list = cenz_info_change.split(',')
#         cenz_comment = request.POST.get('cenz_comment')
#         for program_id in task_ready_list:
#             check_lock = check_oplan3_lock(program_id) or check_planner_lock(program_id)
#             if check_lock and check_lock.get('message') == 'locked' and str(user_id) != str(check_lock.get('worker_id')):
#                 app = check_lock.get('app')
#                 worker_name = check_lock.get('worker_name')
#                 lock_time = check_lock.get('lock_time')
#                 text = f'{program_name(program_id)} заблокирован в {app} пользователем: {worker_name} в {lock_time}.'
#                 error_messages.append(text)
#                 continue
#             custom_fields = cenz_info(program_id)
#             old_values_dict = {
#                 17: custom_fields.get(17),
#                 7: custom_fields.get(7),
#                 14: custom_fields.get(14),
#                 15: custom_fields.get(15),
#                 18: custom_fields.get(18),
#                 19: custom_fields.get(19),
#                 22: custom_fields.get(22),
#                 8: custom_fields.get(8),
#                 9: custom_fields.get(9),
#                 10: custom_fields.get(10),
#                 11: custom_fields.get(11),
#                 12: custom_fields.get(12),
#                 13: custom_fields.get(13),
#                 16: custom_fields.get(16)
#             }
#             work_date = new_values_dict.get(7, old_values_dict.get(7))
#             service_info_dict = {'program_id': program_id, 'user_id': user_id, 'work_date': work_date}
#             # change_db_cenz_info(service_info_dict, old_values_dict, new_values_dict)
#             change_oplan_cenz_info(program_id, old_values_dict, new_values_dict)
#             insert_history(service_info_dict, old_values_dict, new_values_dict)
#             update_comment(program_id, user_id, comment=cenz_comment)
#
#             if task_status:
#                 text = change_task_status(service_info_dict, task_status)
#                 if text.startswith('Ошибка!'):
#                     error_messages.append(text)
#                 else:
#                     success_messages.append(text)
#             else:
#                 text = f'{program_name(program_id)} изменено.'
#                 success_messages.append(text)
#
#         if success_messages:
#             messages.success(request, '\n'.join(success_messages))
#         if error_messages:
#             messages.error(request, '\n'.join(error_messages))
#         if not success_messages and not error_messages:
#             messages.error(request, 'Ошибка!')
#     return redirect(full_list)

def cenz_batch(request):
    success_messages = []
    error_messages = []

    user_id = request.user.id
    data = json.loads(request.body)

    if not data:
        return JsonResponse({'status': 'error', 'message': 'Нет изменений'})
    task_status, task_ready_list, new_values = data
    cenz_comment = new_values.get('cenz_comment')

    for program_id in task_ready_list:
        oplan3_lock = check_oplan3_lock(program_id)
        planner_lock = check_planner_lock(program_id)
        print('check_lock', oplan3_lock)
        if oplan3_lock.get('message') == 'locked':
            text = f'заблокирован в Oplan3 пользователем: {oplan3_lock.get("worker_name")} в {oplan3_lock.get("lock_time")}'
            error_messages.append(text)
            continue
        if planner_lock.get('message') == 'locked':
            text = f'заблокирован в Planner пользователем: {planner_lock.get("worker_name")} в {planner_lock.get("lock_time")}'
            error_messages.append(text)
            continue
        old_values = cenz_info(program_id)

        db_task_status = get_task_status(program_id)
        if db_task_status in ('fix', 'otk_fail', 'final'):
            return JsonResponse(
                {'status': 'error', 'message': f'Ошибка! Изменения не были внесены. Недостаточно прав доступа.'})
        answer = change_task_status_new(program_id, new_values, task_status, db_task_status)
        if answer.get('status') == 'success':
            change_oplan_cenz_info(program_id, old_values, new_values)
            insert_history_new(program_id, user_id, old_values, new_values)
            update_comment(program_id, user_id, task_status, cenz_comment)
            success_messages.append(answer.get('message'))
        else:
            error_messages.append(answer.get('message'))

    if success_messages:
        messages.success(request, '\n'.join(success_messages))
    if error_messages:
        messages.error(request, '\n'.join(error_messages))
    return JsonResponse({'status': 'success', 'message': 'message'})

@login_required()
def material_card(request, program_id):
    user_id = request.user.id
    custom_fields = cenz_info(program_id)
    # process_video_task.delay(program_id)

    # work_date
    if custom_fields.get(7) and not isinstance(custom_fields.get(7), str):
        custom_fields[7] = str(custom_fields.get(7).date())
    if request.method == 'POST':
        form_drop = CenzFormDropDown(request.POST)
        form_text = CenzFormText(request.POST)

        form_attached_files = AttachedFilesForm(request.POST, request.FILES)
        uploaded_file = request.FILES.get('file_path')
        if uploaded_file and uploaded_file.size > 10 * 1024 * 1024:  # 10 МБ
            print(uploaded_file.size)
            # return HttpResponse("Файл слишком большой!", status=400)
        if form_attached_files.is_valid():
            attached_file = form_attached_files.save(commit=False)
            attached_file.owner = user_id
            attached_file.program_id = program_id
            attached_file.save()

    else:
        form_drop = CenzFormDropDown(
            initial={
                'meta_form': custom_fields.get(17),
                'work_date_form': custom_fields.get(7),
                'cenz_rate_form': custom_fields.get(14),
                'engineers_form': custom_fields.get(15),
                'tags_form': custom_fields.get(18),
                'inoagent_form': custom_fields.get(19),
                'narc_select_form':  custom_fields.get(22),
            })
        form_text = CenzFormText(
            initial={
                'lgbt_form': custom_fields.get(8),
                'sig_form': custom_fields.get(9),
                'obnazh_form': custom_fields.get(10),
                'narc_form': custom_fields.get(11),
                'mat_form': custom_fields.get(12),
                'other_form': custom_fields.get(13),
                'editor_form': custom_fields.get(16)
            })
    form_attached_files = AttachedFilesForm()

    attached_files = AttachedFiles.objects.filter(program_id=program_id).order_by('timestamp')
    full_info_dict = full_info(program_id)
    file_id = full_info_dict.get('Files_FileID', '')
    data = {'full_info': full_info_dict,
            'custom_fields': custom_fields,
            'comments_history': comments_history(program_id),
            'deadline': calc_otk_deadline(),
            'schedule_info': schedule_info(program_id),
            'actions_list': select_actions(program_id),
            'filepath_history': select_filepath_history(program_id),
            'attached_files': attached_files,
            'ffmpeg': ffmpeg_dict(file_id),
            'form_text': form_text,
            'form_drop': form_drop,
            'form_attached_files': form_attached_files,
            # 'lock_material': lock_material,
            'permissions': ask_db_permissions(user_id)
            }
    return render(request, 'main/full_info_card.html', data)

def status_ready(request):
    user_id = request.user.id
    new_values = json.loads(request.body)
    if not new_values:
        return JsonResponse({'status': 'error', 'message': 'Нет изменений'})
    program_id = new_values.get('program_id')
    cenz_comment = new_values.get('cenz_comment')
    old_values = cenz_info(program_id)
    task_status = 'ready'

    db_task_status = get_task_status(program_id)
    if db_task_status in ('fix', 'otk_fail', 'final'):
        return JsonResponse({'status': 'error', 'message': f'Ошибка! Изменения не были внесены. Недостаточно прав доступа.'})
    answer = change_task_status_new(program_id, new_values, task_status, db_task_status)
    if answer.get('status') == 'success':
        change_oplan_cenz_info(program_id, old_values, new_values)
        insert_history_new(program_id, user_id, old_values, new_values)
        update_comment(program_id, user_id, task_status, cenz_comment)
    else:
        return JsonResponse(answer)
    message = 'Задача успешно завершена'
    messages.success(request, message)
    return JsonResponse({'status': 'success', 'message': message})

def ask_fix(request):
    user_id = request.user.id
    new_values = json.loads(request.body)
    if not new_values:
        return JsonResponse({'status': 'error', 'message': 'Нет изменений'})
    program_id = new_values.get('program_id')
    task_status = 'fix'
    deadline = new_values.get('deadline')
    fix_comment = new_values.get('fix_comment')
    db_task_status = get_task_status(program_id)

    answer = change_task_status_new(program_id, new_values, task_status, db_task_status)
    if answer.get('status') == 'success':
        create_notification(
            {'sender': user_id, 'recipient': 6, 'program_id': program_id,
             'message': 'Запрос на исправление исходника', 'comment': 'Системное уведомление'}
        )
        update_comment(program_id, user_id, task_status, fix_comment, deadline)
    else:
        return JsonResponse(answer)
    message = 'Заявка на FIX успешно отправлена'
    messages.success(request, message)
    return JsonResponse({'status': 'success', 'message': message})

def cenz_info_change(request):
    user_id = request.user.id
    new_values = json.loads(request.body)
    if not new_values:
        return JsonResponse({'status': 'error', 'message': 'message'})

    program_id = new_values.get('program_id')
    cenz_comment = new_values.get('cenz_comment')
    old_values = cenz_info(program_id)
    db_task_status = get_task_status(program_id)

    task_status = 'no_change'
    answer = change_task_status_new(program_id, new_values, task_status, db_task_status)
    if answer.get('status') == 'success':
        change_oplan_cenz_info(program_id, old_values, new_values)
        insert_history_new(program_id, user_id, old_values, new_values)
        update_comment(program_id, user_id, comment=cenz_comment)
    message = 'Успешно обновлено'
    messages.success(request, message)
    return JsonResponse({'status': 'success', 'message': message})

def check_lock_card(request, program_id):
    try:
        planner_lock = check_planner_lock(program_id)
        oplan3_lock = check_oplan3_lock(program_id)
        return JsonResponse(planner_lock or oplan3_lock)
    except Exception as error:
        return JsonResponse({
            'status': 'error',
            'message': f'Internal server error: {str(error)}'
        }, status=500)

def block_card(request, program_id, user_id):
    try:
        result = block_object_planner(program_id, user_id)
        return JsonResponse(result)
    except Exception as error:
        return JsonResponse({
            'status': 'error',
            'message': f'Internal server error: {str(error)}'
        }, status=500)

def unblock_card(request, program_id, user_id):
    return JsonResponse({'response': unblock_object_planner(program_id, user_id)})

def get_worker_name(request, user_id):
    return JsonResponse({'worker_name': planner_worker_name(user_id)})

def get_movie_poster(request):
    program_id, program_name, year, country = json.loads(request.body)
    if check_db(program_id):
        return JsonResponse({'status': 'success'})
    movie_dict = search({'program_id': program_id, 'title': program_name, 'year': year, 'country': country})
    if not movie_dict:
        return JsonResponse({'status': 'error'})
    return JsonResponse({'status': download_poster(movie_dict['movie']['program_id'], movie_dict['movie']['data-id'])})

@login_required()
def kpi_info(request):
    user_id = request.user.id
    work_date = datetime.today().date()
    workers = ''
    task_status = ''
    material_type = ''
    if request.method == 'POST':
        form = KpiForm(request.POST)
        if form.is_valid():
            work_date = form.cleaned_data.get('work_date_form')
            workers = form.cleaned_data.get('workers_form')
            material_type = form.cleaned_data.get('material_type_form')
            task_status = form.cleaned_data.get('task_status_form')
    else:
        form = KpiForm(initial={
            'work_date_form': str(work_date),
            'workers_form': workers,
            'material_type_form': material_type,
            'task_status': task_status})

    task_list, summary_dict = kpi_summary_calc(
        {'work_date': work_date, 'workers': workers,
         'material_type': material_type, 'task_status': task_status})

    data = {'task_list': task_list,
            'summary_dict': summary_dict,
            'today': datetime.today().date(),
            'form': form,
            'permissions': ask_db_permissions(user_id)}
    return render(request, 'main/kpi_admin_panel.html', data)

@login_required()
def engineer_profile(request, worker_id):
    user_id = request.user.id
    # engineer_id = get_engineer_id(worker_id)
    work_date = datetime.today().date()
    task_status = ''
    material_type = ''
    if request.method == 'POST':
        form = KpiForm(request.POST)
        if form.is_valid():
            work_date = form.cleaned_data.get('work_date_form')
            material_type = form.cleaned_data.get('material_type_form')
            task_status = form.cleaned_data.get('task_status_form')
    else:
        form = KpiForm(initial={
            'work_date_form': str(work_date),
            'material_type': material_type,
            'task_status': task_status})

    task_list, summary_dict = kpi_personal_calc(
        {'work_date': work_date, 'worker_id': worker_id,
         'material_type': material_type, 'task_status': task_status})
# worker_id need to fix
    data = {'worker_id': worker_id,
            'task_list': task_list,
            'summary_dict': summary_dict,
            'today': datetime.today().date(),
            'permissions': ask_db_permissions(user_id),
            'form': form}
    return render(request, 'main/kpi_engineer.html', data)

@login_required()
def work_year_calendar(request, cal_year):
    user_id = request.user.id

    approve_day_off = request.POST.get('approve_day_off', None)
    if approve_day_off:
        insert_day_off(approve_day_off)
    delete_day_off = request.POST.get('delete_day_off', None)
    if delete_day_off:
        drop_day_off(delete_day_off)

    if request.method == 'POST':
        form = VacationForm(request.POST)
        if form.is_valid():
            worker_id = form.cleaned_data['workers_form']
            start_date = form.cleaned_data['start_date_form']
            end_date = form.cleaned_data['end_date_form']
            description = form.cleaned_data['description_form']
            insert_vacation(worker_id, start_date, end_date, description)
        form = VacationForm()
    else:
        form = VacationForm()
    delete_vacation = request.POST.get('delete_vacation', None)
    if delete_vacation:
        drop_vacation(delete_vacation)

    data = {'year_calendar': my_work_calendar(cal_year),
            'prev_year': cal_year-1,
            'year_num': cal_year,
            'next_year': cal_year+1,
            'vacation_list': vacation_info(cal_year),
            'permissions': ask_db_permissions(user_id),
            'form': form}
    return render(request, 'main/work_calendar.html', data)

def work_calendar(request):
    start_year = datetime.today().year
    return redirect(work_year_calendar, start_year)