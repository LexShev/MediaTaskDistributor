import json
import re

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Case, When, BooleanField
from django.http import JsonResponse
from django.shortcuts import render, redirect

from main.permission_pannel import ask_db_permissions
from messenger_static.forms import MessageForm
from .messenger_utils import all_messages, show_viewed_messages, create_notification, find_engineers_name
from .models import Message, Program, Notification, MessageViews


@login_required()
def index(request):
    worker_id = request.user.id
    last_notice = Notification.objects.filter(recipient=worker_id).order_by('-timestamp')[:1] or []
    all_notifications = Notification.objects.filter(recipient=worker_id).order_by('timestamp')[:50] or []
    unread_notifications = Notification.objects.filter(recipient=worker_id, is_read=False).count()
    data = {
        'all_messages': all_messages(worker_id),
        'last_notice': last_notice,
        'all_notifications': all_notifications,
        'unread_notifications': unread_notifications,
        'permissions': ask_db_permissions(worker_id),
    }
    return render(request, 'messenger_static/messenger_empty.html', data)


@login_required()
def messenger(request, program_id):
    worker_id = request.user.id
    if request.method == 'POST':
        form = MessageForm(request.POST, request.FILES)
        if form.is_valid():
            message = form.save(commit=False)
            message.owner = worker_id
            message.program_id = program_id
            message.save()
            MessageViews.objects.create(message=message, worker_id=worker_id)

            message_text = form.cleaned_data.get('message')
            pattern_1 = r'(?<!\w)@([А-ЯЁ][а-яё]+ [А-ЯЁ][а-яё]+)(?!\w)'
            pattern_2 = r'(?<!\w)@([a-zA-Z][a-zA-Z0-9.]*[a-zA-Z0-9])(?=\s|$|[.,!?])'
            mentions = []
            if '@' in message_text:
                mentions = re.findall(pattern_1, message_text, re.UNICODE) or re.findall(pattern_2, message_text, re.UNICODE)
            if mentions:
                for mention in mentions:
                    engineer_id = find_engineers_name(mention)
                    data = {'sender': worker_id, 'recipient': engineer_id, 'program_id': program_id,
                     'message': message_text, 'comment': 'Упоминание в чате'}
                    create_notification(data)

            return redirect('messenger', program_id=program_id)
    form = MessageForm()
    read_message_ids = MessageViews.objects.filter(worker_id=worker_id).values_list('message_id', flat=True)
    messages = Message.objects.filter(program_id=program_id).annotate(
        is_read=Case(When(message_id__in=read_message_ids, then=True), default=False, output_field=BooleanField())
    ).order_by('timestamp')[:50] or []
    program_info = Program.objects.using('oplan3').get(program_id=program_id)

    viewed_messages = show_viewed_messages(program_id, worker_id) or []
    last_notice = Notification.objects.filter(recipient=worker_id).order_by('-timestamp')[:1] or []
    unread_notifications = Notification.objects.filter(recipient=worker_id, is_read=False).count()
    data = {
        'messages': messages,
        'viewed_messages': viewed_messages,
        'all_messages': all_messages(worker_id),
        'last_notice': last_notice,
        'unread_notifications': unread_notifications,
        'program_info': program_info,
        'form': form,
        'permissions': ask_db_permissions(worker_id),
    }

    return render(request, 'messenger_static/messenger.html', data)

def notificator(request):
    worker_id = request.user.id
    last_notice = Notification.objects.filter(recipient=worker_id).order_by('-timestamp')[:1] or []
    all_notifications = Notification.objects.filter(recipient=worker_id).order_by('timestamp')[:50] or []
    unread_notifications = Notification.objects.filter(recipient=worker_id, is_read=False).count()
    data = {
        'all_messages': all_messages(worker_id),
        'last_notice': last_notice,
        'all_notifications': all_notifications,
        'unread_notifications': unread_notifications,
        'permissions': ask_db_permissions(worker_id),
    }
    return render(request, 'messenger_static/notificator.html', data)

def send_notice(request):
    try:
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)
        data = json.loads(request.body)
        if not data:
            return JsonResponse({'status': 'error', 'message': 'No data provided'}, status=400)
        Notification.objects.create(
            sender=data.get('sender'), recipient=data.get('recipient'),
            program_id=data.get('program_id'), message=data.get('message')
        )
        return JsonResponse({'status': 'success', 'message': 'Noticed successfully'})
    except Exception as e:
        print(e)
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

def read_message(request):
    try:
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)
        data = json.loads(request.body)
        worker_id, message_id, program_id = data
        if not data:
            return JsonResponse({'status': 'error', 'message': 'No data provided'}, status=400)

        MessageViews.objects.update_or_create(worker_id=worker_id, message_id=message_id,)
        cur_unread = Message.objects.filter(program_id=program_id).exclude(views__worker_id=worker_id).count()
        total_unread_count = Message.objects.exclude(views__worker_id=worker_id).count()
        unread_notifications = Notification.objects.filter(recipient=worker_id, is_read=False).count()

        return JsonResponse({
            'status': 'success',
            'message': 'Updated successfully',
            'cur_unread': cur_unread,
            'total_unread': total_unread_count + unread_notifications,
        })
    except Exception as e:
        print(e)
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

def read_notice(request):
    try:
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)
        data = json.loads(request.body)
        worker_id, notice_id = data
        if not data:
            return JsonResponse({'status': 'error', 'message': 'No data provided'}, status=400)

        Notification.objects.filter(recipient=worker_id, notice_id=notice_id).update(is_read=True)

        total_unread_count = Message.objects.exclude(views__worker_id=worker_id).count()
        unread_notifications = Notification.objects.filter(recipient=worker_id, is_read=False).count()

        return JsonResponse({
            'status': 'success',
            'message': 'Updated successfully',
            'unread_notifications': unread_notifications,
            'total_unread': total_unread_count + unread_notifications,
        })
    except Exception as e:
        print(e)
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)