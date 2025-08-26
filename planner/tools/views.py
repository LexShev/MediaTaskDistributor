from time import sleep

from django.http import JsonResponse
from django.shortcuts import render

from tools.update_no_material import get_no_material_list


def update_no_material(request):
    try:
        success_list, error_list = get_no_material_list()
        print(success_list, error_list, sep='\n')
        return JsonResponse({'status': 'success', 'message': 'Material updated successfully'})
    except Exception as e:
        print(e)
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
