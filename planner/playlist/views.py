import json
from datetime import date

from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string

from main.permission_pannel import ask_db_permissions
from main.settings.schedule_manager import schedule_manager
from playlist.forms import PlaylistFilter
from playlist.models import PlaylistModel
from playlist.playlist import get_schedule_days, get_schedule_list_by_id, get_schedule_list_by_date


@login_required()
def playlist(request):
    user_id = request.user.id

    try:
        init_dict = PlaylistModel.objects.get(owner=user_id)
    except ObjectDoesNotExist:
        default_filter = PlaylistModel(owner=user_id)
        default_filter.save()
        init_dict = PlaylistModel.objects.get(owner=user_id)
        print("Новый Playlist фильтр создан")

    form = PlaylistFilter(instance=init_dict)

    service_dict = {
        'today': date.today(),
        'schedule_list': schedule_manager.get_all_schedules(),
        'editors_list': schedule_manager.get_all_editors()
    }

    data = {
        'service_dict': service_dict,
        'form': form,
        'permissions': ask_db_permissions(user_id)
    }
    return render(request, 'playlist/index.html', data)

def update_playlist_info(request):
    user_id = request.user.id
    try:
        update_dict = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Неверный формат JSON'}, status=400)
    if not update_dict:
        return JsonResponse({'status': 'error', 'message': 'Нет изменений'})
    try:
        schedule_day_id = update_dict.get('schedule_day_id')
        field_id = update_dict.get('field_id')
        field_name = update_dict.get('field_name')
        value = update_dict.get('value')

        required_fields = ['schedule_day_id', 'field_id', 'field_name', 'value']
        if not all(field in update_dict for field in required_fields):
            return JsonResponse({'status': 'error', 'message': 'Отсутствуют обязательные поля'}, status=400)

        # Пытаемся найти существующую запись
        # playlist_info, created = PlaylistInfo.objects.update_or_create(
        #     schedule_day_id=schedule_day_id,
        #     field_id=field_id,
        #     defaults={
        #         'field_name': field_name,
        #         'value': value,
        #         'last_edit_user_id': user_id,
        #     }
        # )
        #
        # action = 'создана' if created else 'обновлена'
        # return JsonResponse({
        #     'status': 'success',
        #     'message': f'Запись успешно {action}',
        #     'data': {
        #         'id': playlist_info.id,
        #         'schedule_day_id': playlist_info.schedule_day_id,
        #         'field_id': playlist_info.field_id,
        #         'field_name': playlist_info.field_name,
        #         'value': playlist_info.value,
        #         'last_edit_time': playlist_info.last_edit_time
        #     }
        # })
    except IntegrityError as error:
        return JsonResponse({'status': 'error', 'message': 'Конфликт данных: ' + str(error)}, status=409)
    except Exception as error:
        return JsonResponse({'status': 'error', 'message': str(error)}, status=500)

def load_schedule_table(request):
    user_id = request.user.id

    field_dict = json.loads(request.body)
    if not field_dict:
        field_dict = PlaylistModel.objects.filter(owner=user_id).values()
        if field_dict:
            field_dict = field_dict[0]
    schedules = get_schedule_days(field_dict)
    html = render_to_string(
        'playlist/schedule_table.html',
        {
            'schedules': schedules,
        },
        request=request
    )
    return JsonResponse({'html': html})

def update_schedule_filter(request):
    user_id = request.user.id
    values_list = json.loads(request.body)
    schedule_id = values_list.get('schedule_id', '')
    if schedule_id == '':
        schedule_id = None
    if not values_list:
        return JsonResponse({'status': 'error', 'message': 'Нет изменений'})
    PlaylistModel.objects.filter(owner=user_id).update(
        schedule_date=values_list.get('schedule_date'),
        schedule_id=schedule_id
    )
    return JsonResponse({'status': 'success', 'message': 'Обновлено'})

def load_schedule_list_by_id(request):
    user_id = request.user.id
    schedule_day_id = json.loads(request.body)
    if not schedule_day_id:
        return JsonResponse({'status': 'error', 'message': 'No data provided'}, status=400)

    schedule_day_list = get_schedule_list_by_id(schedule_day_id)
    html = render_to_string(
        'playlist/schedule_day_list.html',
        {
            'schedule_day_list': schedule_day_list,
        },
        request=request
    )
    return JsonResponse({'status': 'success', 'message': 'Данные получены', 'html': html})

def get_schedule_info(request):
    try:
        user_id = request.user.id
        schedule_id = json.loads(request.body)
        if not schedule_id:
            return JsonResponse({'status': 'error', 'message': 'No data provided'}, status=400)
        schedule_info = schedule_manager.get_schedule_info(int(schedule_id))
        return JsonResponse({'status': 'success', 'message': 'Данные получены', 'schedule_info': schedule_info})
    except Exception as error:
        return JsonResponse({'status': 'error', 'message': str(error)}, status=500)
def load_schedule_list_by_date(request):
    try:
        user_id = request.user.id
        query = json.loads(request.body)
        if not query:
            return JsonResponse({'status': 'error', 'message': 'No data provided'}, status=400)
        schedule_id = query.get('schedule_id')
        schedule_day_date = query.get('schedule_day_date')
        schedule_day_list = get_schedule_list_by_date(schedule_id, schedule_day_date)
        html = render_to_string(
            'playlist/schedule_day_list.html',
            {
                'schedule_day_list': schedule_day_list,
            },
            request=request
        )
        return JsonResponse({'status': 'success', 'message': 'Данные получены', 'html': html})
    except Exception as error:
        return JsonResponse({'status': 'error', 'message': str(error)}, status=500)