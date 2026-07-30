import json

from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string

from main.form_choices import get_choice
from main.permission_pannel import ask_db_permissions
from main.settings.main_settings import get_main_settings
from .models import AdminModel, TaskSearch
from .admin_materials_list import task_info, process_update_task_list, process_reset_progress, \
    process_add_in_task_list, process_archive_task, process_del_task
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

    try:
        search_init_dict = TaskSearch.objects.get(owner=user_id)
    except ObjectDoesNotExist:
        default_search = TaskSearch(owner=user_id, search_type=1, sql_set=100)
        default_search.save()
        search_init_dict = TaskSearch.objects.get(owner=user_id)

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


@login_required()
def save_filters(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=405)
    user_id = request.user.id
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)

    filter_dict = data.get('filters', {})
    search_dict = data.get('search', {})

    print(f"DEBUG save_filters: user_id={user_id}, filter_dict={filter_dict}, search_dict={search_dict}")

    filter_obj, _ = AdminModel.objects.get_or_create(owner=user_id)
    for field in ['ready_date', 'sched_date', 'deadline', 'worker_id',
                  'material_type', 'sched_id', 'task_status', 'extra_set']:
        val = filter_dict.get(field)
        if val == '':
            val = None
        setattr(filter_obj, field, val)
    filter_obj.save()

    search_obj, _ = TaskSearch.objects.get_or_create(owner=user_id)
    for field in ['search_type', 'search_input', 'sql_set']:
        val = search_dict.get(field)
        if val is not None:
            setattr(search_obj, field, val)
    search_obj.save()

    return JsonResponse({'status': 'success'})


@login_required()
def load_admin_task_table(request):
    user_id = request.user.id
    user_group = request.user.groups.first().id
    page_number = request.GET.get('page', 1)
    field_dict = AdminModel.objects.filter(owner=user_id).values()
    if field_dict:
        field_dict = field_dict[0]
    else:
        field_dict = {}
    search_init_dict = TaskSearch.objects.get(owner=user_id)

    task_list, service_dict = task_info(field_dict, search_init_dict)

    paginator = Paginator(task_list, 50)
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    dynamic_selector_list = []
    workers_list = get_choice().workers()
    task_status_list = get_choice().task_status

    for task in page_obj:
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
            'task_list_zip': zip(page_obj, dynamic_selector_list),
            'service_dict': service_dict,
            'paginator': paginator,
            'page_obj': page_obj,
            'permissions': ask_db_permissions(user_id),
            'tabs': get_main_settings().get_header_panels(user_group)
        },
        request=request
    )
    pagination_html = render_to_string(
        'admin_work_panel/admin_pagination.html',
        {
            'paginator': paginator,
            'page_obj': page_obj,
        },
        request=request
    )
    return JsonResponse({
        'html': html,
        'pagination': pagination_html,
        'order': service_dict.get('order', ''),
        'order_type': service_dict.get('order_type', '')
    })


@login_required()
def sort_table(request):
    user_id = request.user.id
    try:
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)
        data = json.loads(request.body)
        order, order_type = data
        sort_model = TaskSearch.objects.filter(owner=user_id).update(
            order=order,
            order_type=order_type
        )
        if not sort_model == 0:
            return JsonResponse({'status': 'success', 'message': 'Sorted successfully'})
        return JsonResponse({'status': 'error', 'message': 'No data provided'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required()
def batch_action(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=405)
    user_id = request.user.id
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)

    change_type = str(data.get('change_type', ''))
    program_id_check = data.get('program_id_check', [])

    if change_type == '1':
        program_id_list = data.get('program_id', [])
        engineers = data.get('engineers', [])
        work_dates = data.get('work_dates', [])
        new_statuses = data.get('new_statuses', [])
        file_paths = data.get('file_paths', [])
        answer = process_update_task_list(
            user_id, program_id_check, program_id_list,
            engineers, work_dates, new_statuses, file_paths
        )
    elif change_type == '2':
        answer = process_reset_progress(user_id, program_id_check)
    elif change_type == '3':
        program_id_list = data.get('program_id', [])
        work_dates = data.get('work_dates', [])
        answer = process_add_in_task_list(program_id_check, program_id_list, work_dates)
    elif change_type == '4':
        answer = process_archive_task(program_id_check)
    elif change_type == '5':
        answer = process_del_task(program_id_check)
    else:
        return JsonResponse({'status': 'error', 'message': 'Неизвестный тип операции'}, status=400)

    return JsonResponse(answer)
