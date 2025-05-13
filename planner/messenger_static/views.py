from Tools.demo.sortvisu import distinct
from django.db.models import Count
from django.shortcuts import render, redirect

from main.permission_pannel import ask_db_permissions
from messenger_static.forms import MessageForm
from .models import Message


def index(request, program_id):
    worker_id = request.user.id
    print(program_id)
    if request.method == 'POST':
        form = MessageForm(request.POST, request.FILES)
        if form.is_valid():
            message = form.save(commit=False)
            message.owner = worker_id
            message.program_id = program_id
            message.save()
            return redirect('messenger', program_id=program_id)

    form = MessageForm()

    messages = Message.objects.filter(program_id=program_id).order_by('timestamp')[:50]
    prog_count = Message.objects.values('program_id').annotate(count=Count('program_id', distinct=True)).order_by().count()
    prog_filter = Message.objects.filter(program_id=program_id)
    for prog in prog_filter:
        print(prog.program_id, prog.file)


    data = {'permissions': ask_db_permissions(worker_id),
            'messages': messages,
            'program_id': program_id,
            'form': form}

    return render(request, 'messenger_static/messenger_index.html', data)
