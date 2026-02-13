import json
from datetime import date, timedelta

from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from main.permission_pannel import ask_db_permissions
from schedule_perspective.search import fast_search


@login_required()
def schedule_perspective(request):
    user_id = request.user.id
    start_day = date.fromisocalendar(date.today().year, date.today().isocalendar().week, 1)
    schedules = [start_day + timedelta(day) for day in range(7)]
    data = {
        'schedules': schedules,
        'permissions': ask_db_permissions(user_id)
    }
    return render(request, 'schedule_perspective/index.html', data)

def search_program(request):
    try:
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)
        program_name = json.loads(request.body)
        search_list = fast_search(program_name)
        return JsonResponse({
            'status': 'success',
            'message': f'Found {len(search_list)} programs',
            'search_list': search_list,
        })
    except Exception as e:
        print(e)
        return JsonResponse({'status': 'error', 'message': str(e)}, status=405)
