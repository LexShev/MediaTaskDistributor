from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from main.permission_pannel import ask_db_permissions
from messenger_static.messenger_utils import create_notification
from .models import OtkModel, TaskSearch
from .otk_materials_list import task_info, change_task_status_batch, update_comment_batch
from .forms import OtkForm, TaskSearchForm


@login_required()
def work_list(request):
    worker_id = request.user.id
    field_dict = OtkModel.objects.filter(owner=worker_id).values()
    if field_dict:
        field_dict = field_dict[0]
    if worker_id:
        try:
            init_dict = OtkModel.objects.get(owner=worker_id)
        except ObjectDoesNotExist:
            default_filter = OtkModel(owner=worker_id)
            default_filter.save()
            init_dict = OtkModel.objects.get(owner=worker_id)
            print("Новый OtkModel фильтр создан")

        try:
            search_init_dict = TaskSearch.objects.get(owner=worker_id)
        except ObjectDoesNotExist:
            default_search = TaskSearch(owner=worker_id, search_type=1, sql_set=100)
            default_search.save()
            search_init_dict = TaskSearch.objects.get(owner=worker_id)
            print("Новый TaskSearch фильтр создан")

    else:
        init_dict = OtkModel.objects.get(owner=0)
        search_init_dict = TaskSearch.objects.get(owner=0)

    if request.method == 'POST':
        search_form = TaskSearchForm(request.POST, instance=search_init_dict)
        if search_form.is_valid():
            search_form.save()

        approve = request.POST.get('approve_otk')
        otk_fail = request.POST.get('otk_fail')
        approve_fix = request.POST.get('approve_fix')

        if approve:
            program_id_list = request.POST.getlist('program_id')

            change_task_status_batch(program_id_list, 'otk')
            update_comment_batch(program_id_list, 'otk', worker_id)
            print('approve', program_id_list)
        if otk_fail:
            otk_fail_prog_id = request.POST.getlist('otk_fail_prog_id')
            otk_fail_comment = request.POST.getlist('otk_fail_comment')
            engineer_id_list = request.POST.getlist('otk_fail_engineer_id')
            otk_fail_list = []
            for program_id, comment, engineer_id in zip(otk_fail_prog_id, otk_fail_comment, engineer_id_list):
                otk_fail_list.append({'program_id': program_id, 'comment': comment})
                create_notification(
                    {'sender': worker_id, 'recipient': engineer_id, 'program_id': program_id,
                     'message': comment, 'comment': 'Задача отправлена на доработку'}
                )

            change_task_status_batch(otk_fail_list, 'otk_fail')
            update_comment_batch(otk_fail_list, 'otk_fail', worker_id)
            print('otk_fail', otk_fail_list)
        if approve_fix:
            fix_id = request.POST.getlist('fix_prog_id')
            fix_comment = request.POST.getlist('fix_comment')
            fix_file_path = request.POST.getlist('fix_file_path')
            engineer_id_list = request.POST.getlist('fix_engineer_id')
            otk_fix_list = []
            for program_id, comment, file_path, engineer_id in zip(fix_id, fix_comment, fix_file_path, engineer_id_list):
                otk_fix_list.append({'program_id': program_id, 'comment': comment, 'file_path': file_path})
                create_notification(
                    {'sender': worker_id, 'recipient': engineer_id, 'program_id': program_id,
                     'message': comment, 'comment': 'Исходник исправлен'}
                )

            change_task_status_batch(otk_fix_list, 'fix_ready')
            update_comment_batch(otk_fix_list, 'fix_ready', worker_id)
            print('otk_fix_list', otk_fix_list)
        form = OtkForm(request.POST, instance=init_dict)
        if form.is_valid():
            field_vals = [form.cleaned_data.get(field_key) for field_key in form.fields.keys()]
            # field_info = tuple(zip(form.fields.keys(), field_vals))
            field_dict = dict(zip(form.fields.keys(), field_vals))
            form.save()
    else:
        search_form = TaskSearchForm(instance=search_init_dict)
        form = OtkForm(instance=init_dict)
    task_list, service_dict = task_info(field_dict)
    data = {
        'task_list': task_list,
        'service_dict': service_dict,
        'form': form,
        'search_form': search_form,
        'permissions': ask_db_permissions(worker_id)
            }
    return render(request, 'otk/work_list.html', data)
