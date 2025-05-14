from django.db.models import Count
from django.shortcuts import render, redirect

from main.permission_pannel import ask_db_permissions
from messenger_static.forms import MessageForm
from .messenger_utils import unique_program_id, show_messages
from .models import Message


def index(request):
    worker_id = request.user.id
    # prog_count = Message.objects.values('program_id').annotate(
    #     count=Count('program_id', distinct=True)).order_by().count()
    data = {
        'programs_list': unique_program_id(),
        'permissions': ask_db_permissions(worker_id),
    }
    return render(request, 'messenger_static/messenger_index.html', data)

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

    # messages = Message.objects.filter(program_id=program_id).order_by('timestamp')[:50]
    messages, viewed_messages = show_messages(program_id, worker_id)


    data = {'permissions': ask_db_permissions(worker_id),
            'messages': messages,
            'viewed_messages': viewed_messages,
            'program_id': program_id,
            'programs_list': unique_program_id(),
            'form': form}

    return render(request, 'messenger_static/messenger_index.html', data)


