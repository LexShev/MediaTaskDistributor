from django.shortcuts import render
import datetime

from .models import OtkModel
from .work_materials_list import task_info
from .forms import OtkForm


def work_list(request):
    worker_id = request.user.id
    work_date = str(datetime.datetime.today().date())
    work_date = '2025-03-11'
    engineers = ''
    task_status = ''
    material_type = ''
    worker_id = request.user.id
    if worker_id:
        init_dict = OtkModel.objects.get(owner=worker_id)
    else:
        init_dict = OtkModel.objects.get(owner=0)

    if request.method == 'POST':
        form = OtkForm(request.POST, instance=init_dict)
        if form.is_valid():
            print(form)
            sched_date = form.cleaned_data.get('sched_date')
            form.save()
        # if form.is_valid():
        #     work_date = str(form.cleaned_data.get('work_date_form'))
        #     engineers = form.cleaned_data.get('engineers_form')
        #     material_type = form.cleaned_data.get('material_type_form')
        #     task_status = form.cleaned_data.get('task_status_form')
    else:
        sched_date = init_dict.sched_date
        form = OtkForm(instance=init_dict)
        # form = OtkForm(initial={'sched_date': str(sched_date)})
        print('sched_date', sched_date, type(sched_date))
        print(form)
        # initial={
            # 'work_date_form': work_date,
            # 'engineers_form': engineers,
            # 'material_type_form': material_type,
            # 'task_status': task_status}

    work_dates = '2025-03-11'
    data = {'task_list': task_info(work_dates),
            'form': form}
    return render(request, 'otk/work_list.html', data)
