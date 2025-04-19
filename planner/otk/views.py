from django.shortcuts import render
import datetime

from .models import OtkModel
from .otk_materials_list import task_info
from .forms import OtkForm


def work_list(request):
    worker_id = request.user.id
    field_dict = {}
    if worker_id:
        init_dict = OtkModel.objects.get(owner=worker_id)
    else:
        init_dict = OtkModel.objects.get(owner=0)

    if request.method == 'POST':
        form = OtkForm(request.POST, instance=init_dict)
        if form.is_valid():
            field_vals = [form.cleaned_data.get(field_key) for field_key in form.fields.keys()]
            # field_info = tuple(zip(form.fields.keys(), field_vals))
            field_dict = dict(zip(form.fields.keys(), field_vals))
            form.save()
    else:
        sched_date = init_dict.sched_date
        form = OtkForm(instance=init_dict)
        # form = OtkForm(initial={'sched_date': str(sched_date)})
        # field_dict = OtkModel.objects.filter(owner=worker_id)
        # print(field_dict)
    data = {'task_list': task_info(field_dict),
            'form': form}
    return render(request, 'otk/work_list.html', data)
