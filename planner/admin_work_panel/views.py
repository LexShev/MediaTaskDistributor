import json
from datetime import datetime

from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.expressions import result
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string

from main.form_choices import get_choice
from main.permission_pannel import ask_db_permissions
from main.settings.main_settings import get_main_settings
from .models import AdminModel, TaskSearch
from .admin_materials_list import task_info, update_task_list, add_in_task_list, del_task, archive_task, reset_progress
from .forms import AdminForm, DynamicSelector, TaskSearchForm


@login_required()
def task_manager(request):
    user_id = request.user.id
    user_group = request.user.groups.first().id
    try:
        filter_init_dict = AdminModel.objects.get(owner=user_id)
    except ObjectDoesNotExist:
        default_filter = AdminModel(owner=user_id)
        default_filter.save()
        filter_init_dict = AdminModel.objects.get(owner=user_id)
        print("Новый фильтр создан")

    try:
        search_init_dict = TaskSearch.objects.get(owner=user_id)
    except ObjectDoesNotExist:
        default_search = TaskSearch(owner=user_id, search_type=1, sql_set=100)
        default_search.save()
        search_init_dict = TaskSearch.objects.get(owner=user_id)
        print("Новый фильтр создан")

    if request.method == 'POST':
        search_form = TaskSearchForm(request.POST, instance=search_init_dict)
        if search_form.is_valid():
            search_form.save()

        filter_form = AdminForm(request.POST, instance=filter_init_dict)
        if filter_form.is_valid():
            filter_form.save()

        program_id_check = request.POST.getlist('program_id_check')
        change_type = request.POST.get('change_type')

        if program_id_check:
            if change_type == '1':
                answer = update_task_list(request)
                if answer.get('status') == 'success':
                    messages.success(request, answer.get('message'))
                else:
                    messages.error(request, answer.get('message'))
            elif change_type == '2':
                answer = reset_progress(request)
                if answer.get('status') == 'success':
                    messages.success(request, answer.get('message'))
                else:
                    messages.error(request, answer.get('message'))
            elif change_type == '3':
                answer = add_in_task_list(request)
                if answer.get('status') == 'success':
                    messages.success(request, answer.get('message'))
                else:
                    messages.error(request, answer.get('message'))
            elif change_type == '4':
                answer = archive_task(request)
                if answer.get('status') == 'success':
                    messages.success(request, answer.get('message'))
                else:
                    messages.error(request, answer.get('message'))
            elif change_type == '5':
                answer = del_task(request)
                if answer.get('status') == 'success':
                    messages.success(request, answer.get('message'))
                else:
                    messages.error(request, answer.get('message'))
    else:
        filter_form = AdminForm(instance=filter_init_dict)
        search_form = TaskSearchForm(initial={
            'sql_set': search_init_dict.sql_set,
            'search_type': search_init_dict.search_type,
            'order': search_init_dict.order,
            'order_type': search_init_dict.order_type,
        })

    data = {
        'filter_form': filter_form,
        'search_form': search_form,
        'permissions': ask_db_permissions(user_id),
        'tabs': get_main_settings().get_header_panels(user_group)
    }
    return render(request, 'admin_work_panel/task_manager.html', data)

def load_admin_task_table(request):
    user_id = request.user.id
    user_group = request.user.groups.first().id
    field_dict = AdminModel.objects.filter(owner=user_id).values()
    if field_dict: field_dict = field_dict[0]
    search_init_dict = TaskSearch.objects.get(owner=user_id)

    task_list, service_dict = task_info(field_dict, search_init_dict)
    dynamic_selector_list = []
    workers_list = get_choice().workers()
    task_status_list = get_choice().task_status

    for task in task_list:
        file_path = task.get('Task_file_path', '')
        dynamic_selector_list.append(DynamicSelector(
            program_id=task.get('Task_program_id'),
            workers_list=workers_list,
            task_status_list=task_status_list,
            initial={
                'workers_selector': task.get('Task_worker_id'),
                'work_date_selector': task.get('Task_work_date'),
                'status_selector': task.get('Task_task_status'),
                'file_path': file_path or '',
            }),
        )
    html = render_to_string(
        'admin_work_panel/admin_task_table.html',
        {
            'task_list_zip': zip(task_list, dynamic_selector_list),
            'service_dict': service_dict,
            'permissions': ask_db_permissions(user_id),
            'tabs': get_main_settings().get_header_panels(user_group)
        },
        request=request
    )
    return JsonResponse({'html': html})

def sort_table(request):
    user_id = request.user.id
    try:
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)
        data = json.loads(request.body)
        print(data)
        if data:
            order, order_type = data
            sort_model = TaskSearch.objects.filter(owner=user_id).update(
                order=order,
                order_type=order_type
            )
            if not sort_model == 0:
                return JsonResponse({'status': 'success', 'message': 'Sorted successfully', 'data': data})

        return JsonResponse({'status': 'error', 'message': 'No data provided'}, status=400)
    except Exception as e:
        print(e)
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)