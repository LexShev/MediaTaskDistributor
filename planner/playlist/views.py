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
from playlist.playlist import get_schedule_days


@login_required()
def playlist(request):
    user_id = request.user.id
    today = date.today()

    try:
        init_dict = PlaylistModel.objects.get(owner=user_id)
    except ObjectDoesNotExist:
        default_filter = PlaylistModel(owner=user_id)
        default_filter.save()
        init_dict = PlaylistModel.objects.get(owner=user_id)
        print("Новый Playlist фильтр создан")

    form = PlaylistFilter(instance=init_dict)

    schedule_list = (3, 5, 6, 7, 8, 9, 10, 11, 12, 20)
    service_dict = {
        'today': today,
        'cal_month': today.month,
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

    field_dict = PlaylistModel.objects.filter(owner=user_id).values()
    schedules = []

    if field_dict:
        field_dict = field_dict[0]
        try:
            schedules = get_schedule_days(field_dict)
            print('schedules', schedules)
        except Exception as e:
            print(e)
    html = render_to_string(
        'playlist/schedule_table.html',
        {
            'schedules': schedules,
        },
        request=request
    )
    return JsonResponse({'html': html})

def update_playlist_values(request):
    user_id = request.user.id
    values_list = json.loads(request.body)

    if not values_list:
        return JsonResponse({'status': 'error', 'message': 'Нет изменений'})
    PlaylistModel.objects.filter(owner=user_id).update(
        schedule_date=values_list.get('schedule_date'),
        schedule_id=values_list.get('schedule_id')
    )
    return JsonResponse({'status': 'success', 'message': 'Обновлено'})