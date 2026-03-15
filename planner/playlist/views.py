import ast
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
from notifications.models import NotificationRecipient
from playlist.forms import PlaylistFilter
from playlist.models import PlaylistModel, Status, Comment
from playlist.playlist import get_schedule_days, get_schedule_list


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
        'editors_list': schedule_manager.get_editors_with_schedules()
    }

    data = {
        'service_dict': service_dict,
        'form': form,
        'permissions': ask_db_permissions(user_id)
    }
    return render(request, 'playlist/index.html', data)

def update_playlist_status(request):
    user_id = request.user.id
    try:
        update_dict = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Неверный формат JSON'}, status=400)
    if not update_dict:
        return JsonResponse({'status': 'error', 'message': 'Нет изменений'})
    try:
        schedule_day_id = update_dict.get('schedule_day_id')
        status = update_dict.get('status')

        required_fields = ['schedule_day_id', 'status']
        if not all(field in update_dict for field in required_fields):
            return JsonResponse({'status': 'error', 'message': 'Отсутствуют обязательные поля'}, status=400)

        if schedule_day_id is None or status is None:
            return JsonResponse({'status': 'error', 'message': 'Поля не могут быть null'}, status=400)

        # Пытаемся найти существующую запись
        playlist_status, created = Status.objects.update_or_create(
            schedule_day_id=schedule_day_id,
            defaults={
                'status': status,
                'last_edit_user_id': user_id,
            }
        )

        action = 'создана' if created else 'обновлена'
        return JsonResponse({
            'status': 'success',
            'message': f'Запись успешно {action}',
            'data': {
                'schedule_day_id': playlist_status.schedule_day_id,
                'status': playlist_status.status,
                'last_edit_time': playlist_status.last_edit_time
            }
        })
    except IntegrityError as error:
        return JsonResponse({'status': 'error', 'message': 'Конфликт данных: ' + str(error)}, status=409)
    except Exception as error:
        return JsonResponse({'status': 'error', 'message': str(error)}, status=500)

def update_playlist_comment(request):
    user_id = request.user.id
    try:
        update_dict = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Неверный формат JSON'}, status=400)
    if not update_dict:
        return JsonResponse({'status': 'error', 'message': 'Нет изменений'})
    try:
        schedule_day_id = update_dict.get('schedule_day_id')
        comment = update_dict.get('comment', '')

        required_fields = ['schedule_day_id', 'comment']
        if not all(field in update_dict for field in required_fields):
            return JsonResponse({'status': 'error', 'message': 'Отсутствуют обязательные поля'}, status=400)

        if schedule_day_id is None:
            return JsonResponse({'status': 'error', 'message': 'ID канала не может быть null'}, status=400)

        # Пытаемся найти существующую запись
        playlist_comment, created = Comment.objects.update_or_create(
            schedule_day_id=schedule_day_id,
            defaults={
                'comment': comment,
                'last_edit_user_id': user_id,
            }
        )

        action = 'создана' if created else 'обновлена'
        return JsonResponse({
            'status': 'success',
            'message': f'Запись успешно {action}',
            'data': {
                'schedule_day_id': playlist_comment.schedule_day_id,
                'comment': playlist_comment.comment,
                'last_edit_time': playlist_comment.last_edit_time
            }
        })
    except IntegrityError as error:
        return JsonResponse({'status': 'error', 'message': 'Конфликт данных: ' + str(error)}, status=409)
    except Exception as error:
        return JsonResponse({'status': 'error', 'message': str(error)}, status=500)

def load_schedule_table(request):
    user_id = request.user.id

    field_dict = PlaylistModel.objects.filter(owner=user_id).values()
    if field_dict: field_dict = field_dict[0]

    schedules = get_schedule_days(field_dict)
    html = render_to_string(
        'playlist/schedule_table.html',
        {
            'schedules': schedules,
        },
        request=request
    )
    schedule_id_list = ast.literal_eval(field_dict.get('schedule_id') or '[]')
    schedule_info = []
    for schedule_id in schedule_id_list:
        schedule_info.append(schedule_manager.get_schedule_info(int(schedule_id)))

    return JsonResponse({'html': html, 'scheduleInfo': schedule_info})

def update_schedule_filter(request):
    user_id = request.user.id
    try:
        values_list = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Неверный формат JSON'}, status=400)

    if not values_list:
        return JsonResponse({'status': 'error', 'message': 'Нет изменений'})

    update_fields = {}

    # Обработка schedule_date
    if 'schedule_date' in values_list and values_list['schedule_date'] is not None:
        update_fields['schedule_date'] = values_list['schedule_date']

    # Обработка schedule_id (пустую строку превращаем в None)
    if 'schedule_id' in values_list:
        schedule_id = values_list['schedule_id']
        update_fields['schedule_id'] = None if schedule_id == '' else schedule_id

    if not update_fields:
        return JsonResponse({'status': 'error', 'message': 'Нет данных для обновления'}, status=400)

    updated_count = PlaylistModel.objects.filter(owner=user_id).update(**update_fields)

    return JsonResponse({
        'status': 'success',
        'message': f'Обновлено {updated_count} записей'
    })
#
# def load_schedule_list_by_id(request):
#     user_id = request.user.id
#     schedule_day_id = json.loads(request.body)
#     if not schedule_day_id:
#         return JsonResponse({'status': 'error', 'message': 'No data provided'}, status=400)
#
#     schedule_day_list = get_schedule_list_by_id(schedule_day_id)
#     html = render_to_string(
#         'playlist/schedule_day_list.html',
#         {
#             'schedule_day_list': schedule_day_list,
#         },
#         request=request
#     )
#     return JsonResponse({'status': 'success', 'message': 'Данные получены', 'html': html})
#
# def load_schedule_list_by_date(request):
#     try:
#         user_id = request.user.id
#         query = json.loads(request.body)
#         if not query:
#             return JsonResponse({'status': 'error', 'message': 'No data provided'}, status=400)
#         schedule_id = query.get('schedule_id')
#         schedule_day_date = query.get('schedule_day_date')
#         schedule_day_list = get_schedule_list_by_date(schedule_id, schedule_day_date)
#         html = render_to_string(
#             'playlist/schedule_day_list.html',
#             {
#                 'schedule_day_list': schedule_day_list,
#             },
#             request=request
#         )
#         return JsonResponse({'status': 'success', 'message': 'Данные получены', 'html': html})
#     except Exception as error:
#         return JsonResponse({'status': 'error', 'message': str(error)}, status=500)

def load_schedule_list(request):
    try:
        user_id = request.user.id
        query = json.loads(request.body)
        if not query:
            return JsonResponse({'status': 'error', 'message': 'No data provided'}, status=400)

        schedule_day_list = get_schedule_list(query)

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

def editors_notifications(request):
    user_id = request.user.id

    notifications_list = NotificationRecipient.objects.filter(
                recipient=user_id
            ).select_related('notification', 'notification__sender')
    data = {
        'notifications_list': notifications_list,
        'permissions': ask_db_permissions(user_id)
    }
    return render(request, 'playlist/editors_notifications.html', data)