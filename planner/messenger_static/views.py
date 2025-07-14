from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render, redirect

from main.permission_pannel import ask_db_permissions
from messenger_static.forms import MessageForm
from .messenger_utils import show_messages, insert_views, all_messages, show_viewed_messages
from .models import Message, Program, Notification


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
            return redirect('messenger', program_id=program_id)
    form = MessageForm()

    messages = Message.objects.filter(program_id=program_id).order_by('timestamp')[:50] or []
    program_info = Program.objects.using('oplan3').get(program_id=program_id)
    print('program_info', program_info)

    # messages = show_messages(program_id)
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
    # for message, (message_id, worker_id) in zip(messages, viewed_messages):
    #     if message.get('message_id') != message_id:
    #         print(message, message_id, worker_id)

    updated_views = [(message.message_id, worker_id) for message in messages if message.message_id not in viewed_messages]
    print(updated_views)
    if updated_views:
        insert_views(updated_views)
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