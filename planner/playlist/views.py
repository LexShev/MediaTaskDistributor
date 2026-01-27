import json
from datetime import date

from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string

from main.permission_pannel import ask_db_permissions
from playlist.forms import PlaylistFilter
from playlist.models import PlaylistModel
from playlist.playlist import get_schedule_days, get_schedule_day_table


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

    schedule_list = [
        {'schedule_id': 3,
         'editor_id': 17,
         'description': 'Описание'},
        {'schedule_id': 5,
         'editor_id': 40,
         'description': 'Описание'},
        {'schedule_id': 6,
         'editor_id': 12,
         'description': 'Описание'},
        {'schedule_id': 7,
         'editor_id': 17,
         'description': 'Описание'},
        {'schedule_id': 8,
         'editor_id': 12,
         'description': 'Описание'},
        {'schedule_id': 9,
         'editor_id': 40,
         'description': 'Описание'},
        {'schedule_id': 10,
         'editor_id': 15,
         'description': 'Описание'},
        {'schedule_id': 11,
         'editor_id': 12,
         'description': 'Описание'},
        {'schedule_id': 12,
         'editor_id': 17,
         'description': 'Описание'},
        {'schedule_id': 20,
         'editor_id': 16,
         'description': 'Описание'}
    ]
    service_dict = {
        'today': date.today(),
        'schedule_list': schedule_list
    }


    data = {
        'service_dict': service_dict,
        'form': form,
        'permissions': ask_db_permissions(user_id)
    }
    return render(request, 'playlist/index.html', data)

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

def open_schedule_day_table(request):
    user_id = request.user.id
    schedule_day_id = json.loads(request.body)
    if not schedule_day_id:
        return JsonResponse({'status': 'error', 'message': 'No data provided'}, status=400)

    schedule_day_list = get_schedule_day_table(schedule_day_id)
    html = render_to_string(
        'playlist/schedule_day_table.html',
        {
            'schedule_day_list': schedule_day_list,
        },
        request=request
    )
    return JsonResponse({'status': 'success', 'message': 'Данные получены', 'html': html})
