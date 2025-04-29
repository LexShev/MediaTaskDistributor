from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from main.permission_pannel import ask_db_permissions
from .models import OtkModel
from .otk_materials_list import task_info, change_task_status_batch, update_comment_batch
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

        if approve:
            checked_list = request.POST.getlist('program_id')
            program_id_list = [{'program_id': program_id.split(';')[0]} for program_id in checked_list]

            change_task_status_batch(program_id_list, 'otk')
            update_comment_batch(program_id_list, 'otk', worker_id)
            print('approve', program_id_list)
        if otk_fail:
            otk_fail_prog_id = request.POST.getlist('otk_fail_prog_id')
            otk_fail_comment = request.POST.getlist('otk_fail_comment')
            otk_fail_list = []
            for program_id, comment in zip(otk_fail_prog_id, otk_fail_comment):
                otk_fail_list.append({'program_id': program_id, 'comment': comment})

            change_task_status_batch(otk_fail_list, 'otk_fail')
            update_comment_batch(otk_fail_list, 'otk_fail', worker_id)
            print('otk_fail', otk_fail_list)
        if approve_fix:
            fix_id = request.POST.getlist('fix_prog_id')
            fix_comment = request.POST.getlist('fix_comment')
            fix_file_path = request.POST.getlist('fix_file_path')

            otk_fix_list = []
            for program_id, comment, file_path in zip(fix_id, fix_comment, fix_file_path):
                otk_fix_list.append({'program_id': program_id, 'comment': comment, 'file_path': file_path})

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
        form = OtkForm(instance=init_dict)
    task_list, service_dict = task_info(field_dict)
    data = {'task_list': task_list,
            'service_dict': service_dict,
            'form': form,
            'permissions': ask_db_permissions(worker_id)}
    return render(request, 'otk/work_list.html', data)
