from django.shortcuts import render

def day(request):
    return render(request, 'main/day.html')

def week(request):
    return render(request, 'main/week.html')

def month(request):
    return render(request, 'main/month.html')

def full_list(request):
    return render(request, 'main/list.html')
