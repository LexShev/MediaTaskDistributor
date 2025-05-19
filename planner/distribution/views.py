import threading
from django.http import JsonResponse
from django.shortcuts import render, redirect
from .distribution import main_distribution


def start_distribution(request):
    main_distribution()
    return redirect('home')

