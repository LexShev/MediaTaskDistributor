from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from main.permission_pannel import ask_db_permissions
from .common_pool import select_pool, service_pool_info
from .forms import CommonPoolForm
from .models import CommonPool


@login_required()
def common_pool(request):
    worker_id = request.user.id

    if worker_id:
        try:
            init_dict = CommonPool.objects.get(owner=worker_id)
        except ObjectDoesNotExist:
            default_filter = CommonPool(owner=worker_id, sql_set=100)
            default_filter.save()
            init_dict = CommonPool.objects.get(owner=worker_id)
    else:
        init_dict = CommonPool.objects.get(owner=0)

    if request.method == 'POST':
        form = CommonPoolForm(request.POST, instance=init_dict)
        if form.is_valid():
            form.save()
    else:
        form = CommonPoolForm(initial={'sql_set': init_dict.sql_set})

    sql_set = request.POST.get('sql_set', init_dict.sql_set)

    data = {'pool_list': select_pool(sql_set),
            'service_dict': service_pool_info(),
            'permissions': ask_db_permissions(worker_id),
            'form': form,
            }
    return render(request, 'common_pool/common_pool.html', data)