from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string

from main.permission_pannel import ask_db_permissions
from .common_pool import select_pool, get_total_count, get_film_stats, get_season_stats
from .forms import CommonPoolForm
from .models import CommonPool


@login_required()
def common_pool(request):
    worker_id = request.user.id

    if worker_id:
        try:
            init_dict = CommonPool.objects.get(owner=worker_id)
        except ObjectDoesNotExist:
            default_filter = CommonPool(owner=worker_id, search_type=1, sql_set=100)
            default_filter.save()
            init_dict = CommonPool.objects.get(owner=worker_id)
    else:
        init_dict = CommonPool.objects.get(owner=0)

    if request.method == 'POST':
        form = CommonPoolForm(request.POST, instance=init_dict)
        if form.is_valid():
            form.save()
    else:
        form = CommonPoolForm(initial={'sql_set': init_dict.sql_set, 'search_type': init_dict.search_type})

    data = {'pool_list': [],
            'permissions': ask_db_permissions(worker_id),
            'form': form,
            }
    return render(request, 'common_pool/common_pool.html', data)

def total_count(request):
    return JsonResponse(get_total_count())

def film_stats(request):
    return JsonResponse(get_film_stats())

def season_stats(request):
    return JsonResponse(get_season_stats())


def load_pool_table(request):
    worker_id = request.user.id
    if worker_id:
        try:
            init_dict = CommonPool.objects.get(owner=worker_id)
        except ObjectDoesNotExist:
            init_dict = CommonPool.objects.get(owner=worker_id)
    else:
        init_dict = CommonPool.objects.get(owner=0)
    sql_set = request.GET.get('sql_set', init_dict.sql_set)
    html = render_to_string('common_pool/common_pool_table.html', {'pool_list': select_pool(sql_set)})
    return JsonResponse({'html': html})