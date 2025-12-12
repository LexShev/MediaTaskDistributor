import json
from pathlib import PureWindowsPath

from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string

from main.detail_view import insert_filepath_history
from main.logs_and_history import get_task_status, insert_history_status
from main.permission_pannel import ask_db_permissions
from messenger_static.messenger_utils import create_notification
from planner.settings import CURRENT_CENZ_DIR
from .models import OtkModel, TaskSearch
from .otk_materials_list import task_info, change_task_status_batch, update_comment_batch, change_task_status, \
    update_comment
from .forms import OtkForm, TaskSearchForm


@login_required()
def otk(request):
    user_id = request.user.id
    try:
        init_dict = OtkModel.objects.get(owner=user_id)
    except ObjectDoesNotExist:
        default_filter = OtkModel(owner=user_id)
        default_filter.save()
        init_dict = OtkModel.objects.get(owner=user_id)
        print("Новый OtkModel фильтр создан")

    try:
        search_init_dict = TaskSearch.objects.get(owner=user_id)
    except ObjectDoesNotExist:
        default_search = TaskSearch(owner=user_id, search_type=1, sql_set=100)
        default_search.save()
        search_init_dict = TaskSearch.objects.get(owner=user_id)
        print("Новый TaskSearch фильтр создан")

    if request.method == 'POST':
        search_form = TaskSearchForm(request.POST, instance=search_init_dict)
        if search_form.is_valid():
            search_form.save()

        # otk_fail = request.POST.get('otk_fail')
        # approve_fix = request.POST.get('approve_fix')
        #
        # if otk_fail:
        #     otk_fail_prog_id = request.POST.getlist('otk_fail_prog_id')
        #     otk_fail_comment = request.POST.getlist('otk_fail_comment')
        #     worker_id_list = request.POST.getlist('otk_fail_worker_id')
        #     otk_fail_list = []
        #     for program_id, comment, worker_id in zip(otk_fail_prog_id, otk_fail_comment, worker_id_list):
        #         otk_fail_list.append({'program_id': program_id, 'comment': comment})
        #         create_notification(
        #             {'sender': user_id, 'recipient': worker_id, 'program_id': program_id,
        #              'message': comment, 'comment': 'Задача отправлена на доработку'}
        #         )
        #
        #     change_task_status_batch(otk_fail_list, 'otk_fail')
        #     update_comment_batch(otk_fail_list, 'otk_fail', user_id)
        # if approve_fix:
        #     fix_id = request.POST.getlist('fix_program_id')
        #     fix_comment = request.POST.getlist('fix_comment')
        #     fix_file_path = request.POST.getlist('fix_file_path')
        #     worker_id_list = request.POST.getlist('fix_worker_id')
        #     otk_fix_list = []
        #     for program_id, comment, file_path, worker_id in zip(fix_id, fix_comment, fix_file_path, worker_id_list):
        #         otk_fix_list.append({'program_id': program_id, 'comment': comment, 'file_path': file_path})
        #         create_notification(
        #             {'sender': user_id, 'recipient': worker_id, 'program_id': program_id,
        #              'message': comment, 'comment': 'Исходник исправлен'}
        #         )
        #
        #     change_task_status_batch(otk_fix_list, 'fix_ready')
        #     update_comment_batch(otk_fix_list, 'fix_ready', user_id)

        filter_form = OtkForm(request.POST, instance=init_dict)
        if filter_form.is_valid():
            filter_form.save()
    else:
        search_form = TaskSearchForm(instance=search_init_dict)
        filter_form = OtkForm(instance=init_dict)

    settings = {
        'current_cenz_dir': CURRENT_CENZ_DIR
    }
    data = {
        'settings': settings,
        'filter_form': filter_form,
        'search_form': search_form,
        'permissions': ask_db_permissions(user_id)
            }
    return render(request, 'otk/otk.html', data)

def set_status_otk(request):
    success_messages = []
    error_messages = []
    user_id = request.user.id
    program_list = json.loads(request.body)

    if not program_list:
        return JsonResponse({'status': 'error', 'message': 'Нет изменений'})

    task_status = 'otk'
    for program_id, comment, file_name, new_file_name, switch_value in program_list:
        if switch_value == 'cenz':
            new_file_path = str(PureWindowsPath(CURRENT_CENZ_DIR) / new_file_name)
        else:
            new_file_path = str(PureWindowsPath(CURRENT_CENZ_DIR) / new_file_name)

        new_file_path = ''
        create_notification(
            {'sender': user_id, 'recipient': 14, 'program_id': program_id,
             'message': '', 'comment': 'Материал прошёл ОТК'}
        )
        create_notification(
            {'sender': user_id, 'recipient': 15, 'program_id': program_id,
             'message': '', 'comment': 'Материал прошёл ОТК'}
        )
        db_task_status = get_task_status(program_id)
        if db_task_status in ('no_material', 'not_ready'):
            return JsonResponse(
                {'status': 'error', 'message': f'Ошибка! Изменения не были внесены. Недостаточно прав доступа.'})
        answer = change_task_status(program_id, task_status, file_name, new_file_path)
        if answer.get('status') == 'success':
            insert_history_status(program_id, user_id, db_task_status, task_status)
            update_comment(program_id, user_id, task_status, comment)
            # insert_filepath_history(program_id, new_file_path, task_status, user_id)
            success_messages.append(answer.get('message'))
        else:
            error_messages.append(answer.get('message'))
    if success_messages:
        messages.success(request, '\n'.join(success_messages))
    if error_messages:
        messages.error(request, '\n'.join(error_messages))
    return JsonResponse({'status': 'success', 'message': success_messages})

def set_status_fix_ready(request):
    success_messages = []
    error_messages = []
    user_id = request.user.id
    fix_ready_list = json.loads(request.body)

    if not fix_ready_list:
        return JsonResponse({'status': 'error', 'message': 'Нет изменений'})

    task_status = 'fix_ready'

    for program_id, comment, program_name, new_file_path, worker_id in fix_ready_list:
        db_task_status = get_task_status(program_id)
        if db_task_status not in ('fix', 'fix_ready'):
            return JsonResponse(
                {'status': 'error', 'message': f'Ошибка! Изменения не были внесены. Недостаточно прав доступа.'})
        answer = change_task_status(program_id, task_status, program_name, new_file_path)
        if answer.get('status') == 'success':
            insert_history_status(program_id, user_id, db_task_status, task_status)
            update_comment(program_id, user_id, task_status, comment)

            insert_filepath_history(program_id, new_file_path, task_status, user_id)
            success_messages.append(answer.get('message'))
            create_notification(
                {'sender': user_id, 'recipient': worker_id, 'program_id': program_id,
                 'message': comment, 'comment': 'Исходник исправлен'}
            )
        else:
            error_messages.append(answer.get('message'))
    if success_messages:
        messages.success(request, '\n'.join(success_messages))
    if error_messages:
        messages.error(request, '\n'.join(error_messages))
    return JsonResponse({'status': 'success', 'message': success_messages})

def set_status_otk_fail(request):
    success_messages = []
    error_messages = []
    user_id = request.user.id

    otk_fail_list = json.loads(request.body)

    if not otk_fail_list:
        return JsonResponse({'status': 'error', 'message': 'Нет изменений'})

    task_status = 'otk_fail'

    for program_id, comment, program_name, worker_id in otk_fail_list:
        db_task_status = get_task_status(program_id)
        if db_task_status not in ('ready', 'otk', 'otk_fail', 'final_fail'):
            return JsonResponse(
                {'status': 'error', 'message': f'Ошибка! Изменения не были внесены. Недостаточно прав доступа.'})
        answer = change_task_status(program_id, task_status, program_name)
        if answer.get('status') == 'success':
            insert_history_status(program_id, user_id, db_task_status, task_status)
            update_comment(program_id, user_id, task_status, comment)

            success_messages.append(answer.get('message'))
            create_notification(
                {'sender': user_id, 'recipient': worker_id, 'program_id': program_id,
                 'message': comment, 'comment': 'Задача отправлена на доработку'}
            )
        else:
            error_messages.append(answer.get('message'))
    if success_messages:
        messages.success(request, '\n'.join(success_messages))
    if error_messages:
        messages.error(request, '\n'.join(error_messages))
    return JsonResponse({'status': 'success', 'message': success_messages})

def load_otk_task_table(request):
    user_id = request.user.id

    field_dict = OtkModel.objects.filter(owner=user_id).values()
    if field_dict:
        field_dict = field_dict[0]
    search_init_dict = TaskSearch.objects.get(owner=user_id)

    task_list, service_dict = task_info(field_dict, search_init_dict)

    html = render_to_string(
        'otk/otk_task_table.html',
        {
            'task_list': task_list,
            'service_dict': service_dict,
            'permissions': ask_db_permissions(user_id),
        },
        request=request
    )
    return JsonResponse({'html': html})