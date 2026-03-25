import ast
import datetime
import json
from datetime import date

from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from main.permission_pannel import ask_db_permissions
from main.settings.main_settings import main_settings
from main.settings.schedule_manager import schedule_manager
from notifications.models import NotificationRecipient
from notifications.notification_services import create_notification
from playlist.forms import PlaylistFilter, EditorsNotificationFilterForm, EditorsNotificationTaskSearchForm
from playlist.models import PlaylistModel, Status, Comment, EditorsNotificationFilter, EditorsNotificationTaskSearch
from playlist.playlist import get_schedule_days, get_schedule_list, get_schedule_by_schedule_day_id


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
        schedule_info = get_schedule_by_schedule_day_id(schedule_day_id)
        schedule_id = schedule_info.get('schedule_id')
        schedule_name = schedule_info.get("schedule_name")
        schedule_date = schedule_info.get("schedule_date")
        if schedule_date and isinstance(schedule_date, datetime.datetime):
            schedule_date = schedule_date.date().strftime('%d-%m-%Y')

        try:
            message = f'Статус плейлиста {schedule_name} на {schedule_date} изменён'
            create_notification(request.user, (1,),
                                message=message,
                                comment=f'Статус изменён на "{main_settings.get_oplan_channels_dict(status)}"',
                                notification_type='status',
                                schedule_id=schedule_id)
        except Exception as error:
            return JsonResponse({'status': 'error', 'message': str(error)}, status=500)

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

        schedule_info = get_schedule_by_schedule_day_id(schedule_day_id)
        schedule_id = schedule_info.get('schedule_id')
        schedule_name = schedule_info.get("schedule_name")
        schedule_date = schedule_info.get("schedule_date")
        if schedule_date and isinstance(schedule_date, datetime.datetime):
            schedule_date = schedule_date.date().strftime('%d-%m-%Y')

        try:
            message = f'Добавлен комментарий для {schedule_name} на {schedule_date}'
            create_notification(request.user, (1,),
                                message=message,
                                comment=comment, notification_type='info',
                                schedule_id=schedule_id)
        except Exception as error:
            return JsonResponse({'status': 'error', 'message': str(error)}, status=500)

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

    try:
        filter_init_dict = EditorsNotificationFilter.objects.get(owner=user_id)
    except ObjectDoesNotExist:
        default_filter = EditorsNotificationFilter(owner=user_id)
        default_filter.save()
        filter_init_dict = EditorsNotificationFilter.objects.get(owner=user_id)
        print("Новый фильтр создан")

    filter_form = EditorsNotificationFilterForm(instance=filter_init_dict)

    try:
        search_init_dict = EditorsNotificationTaskSearch.objects.get(owner=user_id)
    except ObjectDoesNotExist:
        default_search = EditorsNotificationTaskSearch(owner=user_id)
        default_search.save()
        search_init_dict = EditorsNotificationTaskSearch.objects.get(owner=user_id)
        print("Новый фильтр создан")

    search_form = EditorsNotificationTaskSearchForm(instance=search_init_dict)

    data = {
        'filter_form': filter_form,
        'search_form': search_form,
        'permissions': ask_db_permissions(user_id)
    }
    return render(request, 'playlist/editors_notifications.html', data)

def load_notification_list(request):
    try:
        user_id = request.user.id

        notification_params = json.loads(request.body)
        if not notification_params:
            return JsonResponse({'status': 'error', 'message': 'No data provided'}, status=400)

        page_number = notification_params.get('page_number', 1)

        search_input = notification_params.get('search_input')

        try:
            filter_init_dict = EditorsNotificationFilter.objects.get(owner=user_id)
        except EditorsNotificationFilter.DoesNotExist:
            filter_init_dict = None

        notifications_list = NotificationRecipient.objects.filter(
            recipient=user_id
        ).select_related('notification', 'notification__sender')

        filters = Q()

        # Применяем фильтры через Q объекты (на уровне БД)
        if filter_init_dict:

            if filter_init_dict.worker_id:
                filters &= Q(notification__sender_id=filter_init_dict.worker_id)

            if filter_init_dict.notification_type:
                filters &= Q(notification__notification_type=filter_init_dict.notification_type)

            if filter_init_dict.sched_id:
                filters &= Q(notification__schedule_id=filter_init_dict.sched_id)

            if filter_init_dict.notification_time:
                filters &= Q(notification__timestamp__date=filter_init_dict.notification_time)

            if filter_init_dict.is_read is not None:
                filters &= Q(is_read=filter_init_dict.is_read)

        if search_input is not None:
            filters &= Q(notification__message__icontains=search_input.strip())

        # Применяем все фильтры одним запросом
        if filters:
            notifications_list = notifications_list.filter(filters)

        # Сортируем на уровне БД
        notifications_list = notifications_list.order_by('-notification__timestamp')

        # Пагинация
        paginator = Paginator(notifications_list, 18)

        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        html = render_to_string(
            'playlist/editors_notification_list.html',
            {
                'notifications_list': page_obj,
                'page_obj': page_obj,
                'paginator': paginator,
            },
            request=request
        )
        return JsonResponse({'status': 'success', 'message': 'Данные получены', 'html': html})
    except Exception as error:
        return JsonResponse({'status': 'error', 'message': str(error)}, status=500)

def update_editors_notification_filter(request):
    user_id = request.user.id

    try:
        update_dict = json.loads(request.body)
        if not update_dict:
            return JsonResponse({'status': 'error', 'message': 'Нет изменений'})

        filter_key = update_dict.get('filter_key')
        filter_value = update_dict.get('filter_value')

        required_fields = ['filter_key', 'filter_value']
        if not all(field in update_dict for field in required_fields):
            return JsonResponse({'status': 'error', 'message': 'Отсутствуют обязательные поля'}, status=400)

        # Пытаемся найти существующую запись
        filter_obj, created = EditorsNotificationFilter.objects.get_or_create(
            owner=user_id,
            defaults={
                'notification_time': None,
                'worker_id': None,
                'notification_type': None,
                'sched_id': None
            }
        )

        # Обновляем конкретное поле в зависимости от filter_key
        if filter_key == 'worker_id':
            filter_obj.worker_id = int(filter_value) if filter_value else None
        elif filter_key == 'notification_type':
            filter_obj.notification_type = filter_value if filter_value else None
        elif filter_key == 'sched_id':
            filter_obj.sched_id = int(filter_value) if filter_value else None
        elif filter_key == 'notification_time':
            filter_obj.notification_time = filter_value if filter_value else None
        elif filter_key == 'is_read':
            if filter_value is None or filter_value == '':
                filter_obj.is_read = None
            else:
                if isinstance(filter_value, str):
                    filter_obj.is_read = filter_value.lower() in ['1', 'true']
                elif isinstance(filter_value, bool):
                    filter_obj.is_read = filter_value
                elif isinstance(filter_value, (int, float)):
                    filter_obj.is_read = bool(filter_value)
                else:
                    filter_obj.is_read = None
        else:
            return JsonResponse({'status': 'error', 'message': f'Неизвестный ключ фильтра: {filter_key}'}, status=400)

        filter_obj.save()

        action = 'создана' if created else 'обновлена'
        return JsonResponse({
            'status': 'success',
            'message': f'Фильтр "{filter_key}" успешно {action}',
            'data': {
                'filter_key': filter_key,
                'filter_value': filter_value
            }
        })
    except Exception as error:
        return JsonResponse({'status': 'error', 'message': str(error)}, status=500)
