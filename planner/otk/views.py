from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from main.permission_pannel import ask_db_permissions
from .models import OtkModel
from .otk_materials_list import task_info, change_task_status_batch, update_comment_batch, change_task_status_fix, \
    update_comment_fix, change_task_status_otk_fail, update_comment_otk_fail
from .forms import OtkForm


@login_required()
def work_list(request):
    worker_id = request.user.id
    field_dict = OtkModel.objects.filter(owner=worker_id).values()
    if field_dict:
        field_dict = field_dict[0]
    if worker_id:
        init_dict = OtkModel.objects.get(owner=worker_id)
    else:
        init_dict = OtkModel.objects.get(owner=0)

    if request.method == 'POST':
        approve = request.POST.get('approve_otk')
        otk_fail = request.POST.get('otk_fail')
        approve_fix = request.POST.get('approve_fix')
        program_id_tuple = request.POST.getlist('program_id')
        print('program_id_list', program_id_tuple)

        fix_id = request.POST.getlist('fix_prog_id')
        fix_comment = request.POST.getlist('fix_comment')
        fix_file_path = request.POST.getlist('fix_file_path')
        fix_tuple = list(zip(fix_id, fix_comment, fix_file_path))

        otk_fail_prog_id = request.POST.getlist('otk_fail_prog_id')
        otk_fail_comment = request.POST.getlist('otk_fail_comment')
        otk_fail_tuple = list(zip(otk_fail_prog_id, otk_fail_comment))




        if approve:
            change_task_status_batch(program_id_tuple, 'otk')
            update_comment_batch(program_id_tuple, 'otk', worker_id)
            print('approve', program_id_tuple)
        if otk_fail:
            change_task_status_otk_fail(otk_fail_tuple, 'otk_fail')
            update_comment_otk_fail(otk_fail_tuple, 'otk_fail', worker_id)
            print('otk_fail', otk_fail_tuple)
        if approve_fix:
            change_task_status_fix(fix_tuple, 'fix_ready')
            update_comment_fix(fix_tuple, 'fix_ready', worker_id)
            print('fix_tuple', fix_tuple)
        form = OtkForm(request.POST, instance=init_dict)
        if form.is_valid():
            field_vals = [form.cleaned_data.get(field_key) for field_key in form.fields.keys()]
            # field_info = tuple(zip(form.fields.keys(), field_vals))
            field_dict = dict(zip(form.fields.keys(), field_vals))
            form.save()
    else:
        form = OtkForm(instance=init_dict)
    task_list, service_dict = task_info(field_dict)
    data = {'task_list': task_list,
            'service_dict': service_dict,
            'form': form,
            'permissions': ask_db_permissions(worker_id)}
    return render(request, 'otk/work_list.html', data)
