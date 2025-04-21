from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from main.permission_pannel import ask_db_permissions
from .models import OtkModel
from .otk_materials_list import task_info
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
        fix_otk = request.POST.get('fix_otk')
        if approve:
            program_id = request.POST.getlist('program_id')
            print('approve', program_id)
        if fix_otk:
            program_id = request.POST.getlist('program_id')
            print('fix', program_id)
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
