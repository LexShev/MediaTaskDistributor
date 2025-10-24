import threading
from django.http import JsonResponse
from django.shortcuts import render, redirect
from .distribution import main_distribution


def start_distribution(request):
    try:
        result = main_distribution()
        if result.get('status') == 'success':
            return JsonResponse(result)
        else:
            return JsonResponse(result, status=405)
    except Exception as e:
        print(e)
        return JsonResponse({'status': 'error', 'message': str(e)}, status=405)

