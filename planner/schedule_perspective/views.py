import json
from datetime import date, timedelta

from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from main.permission_pannel import ask_db_permissions
from main.settings.main_settings import get_main_settings
from schedule_perspective.program_info import get_program_info, update_schedule_info
from schedule_perspective.search import fast_search, search_kinopoisk


@login_required()
def schedule_perspective(request):
    user_id = request.user.id
    user_group = request.user.groups.first().id
    start_date = date.fromisocalendar(date.today().year, date.today().isocalendar().week, 1)
    # schedules = [start_date + timedelta(day) for day in range(7)]
    start_date = date(2026, 11, 2)
    schedule_id = 3
    data = {
        'schedules': get_program_info(start_date, schedule_id),
        'permissions': ask_db_permissions(user_id),
        'tabs': get_main_settings().get_header_panels(user_group)
    }
    return render(request, 'schedule_perspective/index.html', data)


def search_program(request):
    try:
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)
        program_name = json.loads(request.body)
        search_list = fast_search(program_name)
        kinopoisk_list = search_kinopoisk(program_name)

        # Убираем дубликаты из kinopoisk, если такие же названия есть в oplan
        oplan_titles = {item.get('Progs_name', '').lower() for item in search_list}
        filtered_kinopoisk = [
            item for item in kinopoisk_list
            if item.get('title', '').lower() not in oplan_titles
        ]

        return JsonResponse({
            'status': 'success',
            'message': f'Found {len(search_list)} oplan programs, {len(filtered_kinopoisk)} kinopoisk programs',
            'search_list': search_list,
            'kinopoisk_list': filtered_kinopoisk,
        })
    except Exception as e:
        print(e)
        return JsonResponse({'status': 'error', 'message': str(e)}, status=405)


def update_program_position(request):
    try:
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)
        data = json.loads(request.body)
        if not data:
            return JsonResponse({'status': 'error', 'message': 'No data provided'}, status=400)
        schedule_id = 3
        oplan_program_id = data.get('oplanProgramId')
        kinopoisk_id = data.get('kinopoiskId')
        from_container = data['fromContainer']
        to_container = data['toContainer']
        old_index = data['oldIndex']
        new_index = data['newIndex']

        print('oplan_program_id', oplan_program_id)
        print('kinopoisk_id', kinopoisk_id)
        print('from_container', from_container)
        print('to_container', to_container)
        print('old_index', old_index)
        print('new_index', new_index)

        if oplan_program_id:
            result = update_schedule_info(schedule_id, oplan_program_id, from_container, to_container, old_index,
                                          new_index)
            if not result.get('status') == 'success':
                return JsonResponse({'status': 'error', 'message': result['message']}, status=400)
            return JsonResponse({'success': True})

        # Если это kinopoisk карточка - просто добавляем в расписание с флагом
        # (пока заглушка, так как для kinopoisk нужно будет позже создавать запись в planner)
        return JsonResponse({'success': True})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)