import json

from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.db import connections
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string

from main.permission_pannel import ask_db_permissions
from .common_pool import select_pool, get_total_count, get_film_stats, get_season_stats, insert_in_common_task, \
    insert_in_task_list
from .forms import CommonPoolForm
from .models import CommonPool


@login_required()
def common_pool(request):
    user_id = request.user.id

    try:
        init_dict = CommonPool.objects.get(owner=user_id)
    except ObjectDoesNotExist:
        default_filter = CommonPool(owner=user_id, search_type=1, sql_set=100)
        default_filter.save()
        init_dict = CommonPool.objects.get(owner=user_id)

    if request.method == 'POST':
        form = CommonPoolForm(request.POST, instance=init_dict)
        if form.is_valid():
            form.save()
    else:
        form = CommonPoolForm(
            initial={'sql_set': init_dict.sql_set, 'search_type': init_dict.search_type}
        )

    data = {'pool_list': [],
            'permissions': ask_db_permissions(user_id),
            'form': form,
            }
    return render(request, 'common_pool/common_pool.html', data)

def total_count(request):
    return JsonResponse(get_total_count())

def film_stats(request):
    return JsonResponse(get_film_stats())

def season_stats(request):
    return JsonResponse(get_season_stats())

def add_in_task_list(request):
    user_id = request.user.id
    try:
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)
        data = json.loads(request.body)
        if not data:
            return JsonResponse({'status': 'error', 'message': 'No data provided'}, status=400)
        sched_id, program_id_list, work_date = data
        result = {}
        if sched_id == 1:
            result = insert_in_common_task(data)
        elif sched_id == 99:
            result = insert_in_task_list(user_id, data)
        if result.get('status') == 'success':
            message = result.get('message')
            messages.success(request, message)
            return JsonResponse({'status': 'success', 'message': message})
        else:
            return JsonResponse({
                'status': 'error', 'message': result.get('message'), 'busy_list': result.get('busy_list')
            }, status=400)
    except Exception as e:
        print(e)
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

def load_pool_table(request):
    user_id = request.user.id
    try:
        init_dict = CommonPool.objects.get(owner=user_id)
    except ObjectDoesNotExist:
        init_dict = CommonPool.objects.get(owner=user_id)

    sql_set = request.GET.get('sql_set', init_dict.sql_set)
    html = render_to_string(
        'common_pool/common_pool_table.html',
        {'pool_list': select_pool(sql_set),
         'permissions': ask_db_permissions(user_id),
         },
        request=request
    )
    return JsonResponse({'html': html})