from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from desktop.desktop_list import task_info
from main.permission_pannel import ask_db_permissions


@login_required()
def show_desktop(request):
    worker_id = request.user.id
    # search_query = request.GET.get('fast_search', None)
    start_date, end_date = '2025-03-10', '2025-03-29'
    data = {
        'permissions': ask_db_permissions(worker_id),
        'task_list': task_info(worker_id, start_date, end_date)
    }
    return render(request, 'desktop/index.html', data)