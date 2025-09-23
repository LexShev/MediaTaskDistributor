from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string

from main.permission_pannel import ask_db_permissions
from messenger_static.messenger_utils import create_notification
from .models import OtkModel, TaskSearch
from .otk_materials_list import task_info, change_task_status_batch, update_comment_batch
from .forms import OtkForm, TaskSearchForm


@login_required()
def otk(request):
    user_id = request.user.id
    # field_dict = OtkModel.objects.filter(owner=user_id).values()
    # if field_dict:
    #     field_dict = field_dict[0]
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

        approve = request.POST.get('approve_otk')
        otk_fail = request.POST.get('otk_fail')
        approve_fix = request.POST.get('approve_fix')
        approve_final_fail = request.POST.get('approve_final_fail')

        if approve:
            program_id_list = request.POST.getlist('program_id_check')
            approve_list = [{'program_id': program_id} for program_id in program_id_list]
            change_task_status_batch(approve_list, 'otk')
            update_comment_batch(approve_list, 'otk', user_id)
        if otk_fail:
            otk_fail_prog_id = request.POST.getlist('otk_fail_prog_id')
            otk_fail_comment = request.POST.getlist('otk_fail_comment')
            worker_id_list = request.POST.getlist('otk_fail_worker_id')
            otk_fail_list = []
            for program_id, comment, worker_id in zip(otk_fail_prog_id, otk_fail_comment, worker_id_list):
                otk_fail_list.append({'program_id': program_id, 'comment': comment})
                create_notification(
                    {'sender': user_id, 'recipient': worker_id, 'program_id': program_id,
                     'message': comment, 'comment': 'Задача отправлена на доработку'}
                )

            change_task_status_batch(otk_fail_list, 'otk_fail')
            update_comment_batch(otk_fail_list, 'otk_fail', user_id)
        if approve_fix:
            fix_id = request.POST.getlist('fix_prog_id')
            fix_comment = request.POST.getlist('fix_comment')
            fix_file_path = request.POST.getlist('fix_file_path')
            worker_id_list = request.POST.getlist('fix_worker_id')
            otk_fix_list = []
            for program_id, comment, file_path, worker_id in zip(fix_id, fix_comment, fix_file_path, worker_id_list):
                otk_fix_list.append({'program_id': program_id, 'comment': comment, 'file_path': file_path})
                create_notification(
                    {'sender': user_id, 'recipient': worker_id, 'program_id': program_id,
                     'message': comment, 'comment': 'Исходник исправлен'}
                )

            change_task_status_batch(otk_fix_list, 'fix_ready')
            update_comment_batch(otk_fix_list, 'fix_ready', user_id)

        filter_form = OtkForm(request.POST, instance=init_dict)
        if filter_form.is_valid():
            # field_vals = [form.cleaned_data.get(field_key) for field_key in form.fields.keys()]
            # field_dict = dict(zip(form.fields.keys(), field_vals))
            filter_form.save()
    else:
        search_form = TaskSearchForm(initial={'sql_set': search_init_dict.sql_set, 'search_type': search_init_dict.search_type})
        filter_form = OtkForm(instance=init_dict)
    data = {
        'filter_form': filter_form,
        'search_form': search_form,
        'permissions': ask_db_permissions(user_id)
            }
    return render(request, 'otk/otk.html', data)

def load_otk_task_table(request):
    user_id = request.user.id

    field_dict = OtkModel.objects.filter(owner=user_id).values()
    if field_dict:
        field_dict = field_dict[0]
    search_init_dict = TaskSearch.objects.get(owner=user_id)

    task_list, service_dict = task_info(field_dict, search_init_dict.sql_set)

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