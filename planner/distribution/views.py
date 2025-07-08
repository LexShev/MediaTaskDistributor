import threading
from django.http import JsonResponse
from django.shortcuts import render, redirect
from .distribution import main_distribution


def start_distribution(request):
    try:
        main_distribution()
        return JsonResponse({'status': 'success', 'message': ''})
    except Exception as e:
        print(e)
        return JsonResponse({'status': 'error', 'message': str(e)}, status=405)

