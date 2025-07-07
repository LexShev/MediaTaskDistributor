from datetime import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from main.permission_pannel import ask_db_permissions
from .models import AdminModel, TaskSearch
from .admin_materials_list import task_info, update_task_list, add_in_common_task, del_task
from .forms import AdminForm, DynamicSelector, TaskSearchForm


@login_required()
def task_manager(request):
    worker_id = request.user.id
    field_dict = AdminModel.objects.filter(owner=worker_id).values()
    if field_dict: field_dict = field_dict[0]
    if worker_id:
        try:
            filter_init_dict = AdminModel.objects.get(owner=worker_id)
        except ObjectDoesNotExist:
            default_filter = AdminModel(owner=worker_id)
            default_filter.save()
            filter_init_dict = AdminModel.objects.get(owner=worker_id)
            print("Новый фильтр создан")

        try:
            search_init_dict = TaskSearch.objects.get(owner=worker_id)
        except ObjectDoesNotExist:
            default_search = TaskSearch(owner=worker_id, search_type=1, sql_set=100)
            default_search.save()
            search_init_dict = TaskSearch.objects.get(owner=worker_id)
            print("Новый фильтр создан")
    else:
        filter_init_dict = AdminModel.objects.get(owner=0)
        search_init_dict = TaskSearch.objects.get(owner=0)

    if request.method == 'POST':
        search_form = TaskSearchForm(request.POST, instance=search_init_dict)
        if search_form.is_valid():
            search_form.save()

        filter_form = AdminForm(request.POST, instance=filter_init_dict)
        if filter_form.is_valid():
            field_vals = [filter_form.cleaned_data.get(field_key) for field_key in filter_form.fields.keys()]
            # field_info = tuple(zip(form.fields.keys(), field_vals))
            field_dict = dict(zip(filter_form.fields.keys(), field_vals))
            filter_form.save()

        program_id_check = request.POST.getlist('program_id_check')
        print('program_id_check', program_id_check)
        change_type = request.POST.get('change_type')

        if program_id_check:
            if change_type == '1':
                update_task_list(request)
            elif change_type == '2':
                add_in_common_task(request)
            elif change_type == '3':
                del_task(request)

    else:
        filter_form = AdminForm(instance=filter_init_dict)
        search_form = TaskSearchForm(instance=search_init_dict)
    print(field_dict, search_init_dict.sql_set)
    task_list, service_dict = task_info(field_dict, search_init_dict.sql_set)
    dynamic_selector_list = []
    for task in task_list:
        file_path = task.get('Task_file_path', '')
        dynamic_selector_list.append(DynamicSelector(
            program_id=task.get('Task_program_id'),
            initial={'engineers_selector': task.get('Task_engineer_id'),
                     'work_date_selector': task.get('Task_work_date'),
                     'status_selector': task.get('Task_task_status'),
                     'file_path': file_path or '',
                     }),
        )
    data = {
        'task_list_zip': zip(task_list, dynamic_selector_list),
        'service_dict': service_dict,
        'filter_form': filter_form,
        'search_form': search_form,
        'permissions': ask_db_permissions(worker_id)
    }
    return render(request, 'admin_work_panel/task_manager.html', data)

