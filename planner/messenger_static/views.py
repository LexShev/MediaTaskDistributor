from django.shortcuts import render



def index(request):
    return render(request, 'messenger_static/messenger_index.html')
