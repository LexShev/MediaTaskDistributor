from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

def my_view(request):
    return render(request, 'authenticate/login.html')

def login_worker(request):
    next_request = request.GET.get('next')
    if request.method == 'POST':
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if next_request:
                return redirect(next_request)
            else:
                homepage_dict = {0: 'home',
                                 1: 'month',
                                 2: 'home'}
                return redirect(homepage_dict.get(request.user.id, 0))
        else:
            messages.success(request, 'Неверный логин или пароль')
            return redirect('login_worker')

    return render(request, 'authenticate/login.html')

def logout_worker(request):
    logout(request)
    messages.success(request, 'Вы вышли из системы')
    return redirect('login_worker')
