import ast
import json
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render

from desktop.desktop_list import task_info, cards_container
from desktop.forms import DeskTopFilter
from desktop.models import ModelDeskTopFilter, ModelCardsContainer
from main.permission_pannel import ask_db_permissions


@login_required()
def show_desktop(request):
    schedules = (1, 3, 5, 6, 7, 8, 9, 10, 11, 12, 20)
    start_date = datetime.today()
    work_dates = (start_date, start_date)
    task_status = ('not_ready', 'ready', 'fix')
    material_type = ('film', 'season')
    worker_id = request.user.id
    if worker_id:
        try:
            inst_dict = ModelDeskTopFilter.objects.get(owner=worker_id)
        except ObjectDoesNotExist:


            default_filter = ModelDeskTopFilter(
                owner=worker_id, schedules=schedules,
                material_type=material_type,
                work_dates=' - '.join([work_date.strftime('%d.%m.%Y') for work_date in work_dates]),
                task_status=task_status
            )

            default_filter.save()
            inst_dict = ModelDeskTopFilter.objects.get(owner=worker_id)
            print("Новый фильтр создан")

    else:
        inst_dict = ModelDeskTopFilter.objects.get(owner=0)

    if request.method == 'POST':
        desktop_form = DeskTopFilter(request.POST, instance=inst_dict)
        if desktop_form.is_valid():
            desktop_form.save()

            schedules = ast.literal_eval(desktop_form.cleaned_data.get('schedules'))
            material_type = ast.literal_eval(desktop_form.cleaned_data.get('material_type'))
            work_dates = tuple(
                map(lambda d: datetime.strptime(d, '%d.%m.%Y'), desktop_form.cleaned_data.get('work_dates').split(' - ')))
            task_status = ast.literal_eval(desktop_form.cleaned_data.get('task_status'))

    else:
        schedules = ast.literal_eval(inst_dict.schedules)
        material_type = ast.literal_eval(inst_dict.material_type)
        work_dates = tuple(map(lambda d: datetime.strptime(d, '%d.%m.%Y'), inst_dict.work_dates.split(' - ')))
        task_status = ast.literal_eval(inst_dict.task_status)

        initial_dict = {'schedules': schedules,
                        'material_type': material_type,
                        'work_dates': ' - '.join([work_date.strftime('%d.%m.%Y') for work_date in work_dates]),
                        'task_status': task_status}
        desktop_form = DeskTopFilter(initial=initial_dict)
    cards_list_01 = tuple(ModelCardsContainer.objects.filter(container=1, owner=worker_id).values_list('program_id', flat=True))
    cards_list_02 = tuple(ModelCardsContainer.objects.filter(container=2, owner=worker_id).values_list('program_id', flat=True))
    exclusion_list = cards_list_01 + cards_list_02
    data = {
        'permissions': ask_db_permissions(worker_id),
        'full_list': task_info(worker_id, schedules, material_type, task_status, work_dates, exclusion_list),
        'cards_container_01': cards_container(cards_list_01),
        'cards_container_02': cards_container(cards_list_02),
        'desktop_form': desktop_form,
    }
    return render(request, 'desktop/index.html', data)


def update_order(request):
    worker_id = request.user.id
    try:
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)
        data = json.loads(request.body)
        order_01 = data.get('order_01', [])
        order_02 = data.get('order_02', [])

        if not data:
            return JsonResponse({'status': 'error', 'message': 'No order data provided'}, status=400)

        with transaction.atomic():
            ModelCardsContainer.objects.filter(owner=worker_id).delete()
            programs_01 = [ModelCardsContainer(container=1, owner=worker_id, order=num, program_id=program_id) for num, program_id in enumerate(order_01)]
            programs_02 = [ModelCardsContainer(container=2, owner=worker_id, order=num, program_id=program_id) for num, program_id in enumerate(order_02)]
            ModelCardsContainer.objects.bulk_create(programs_01)
            ModelCardsContainer.objects.bulk_create(programs_02)
        return JsonResponse({'status': 'success', 'message': 'Order updated successfully'})
    except Exception as e:
        print(e)
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

