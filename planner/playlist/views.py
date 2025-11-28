from datetime import date

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from main.permission_pannel import ask_db_permissions


@login_required()
def playlist(request):
    user_id = request.user.id
    today = date.today()
    service_dict = {
        'today': today,
        'cal_month': today.month,
    }
    data = {
        'service_dict': service_dict,
        'permissions': ask_db_permissions(user_id)
    }
    return render(request, 'playlist/index.html', data)
