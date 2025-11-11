import json

from django.http import JsonResponse
from django.shortcuts import render

from main.permission_pannel import ask_db_permissions
from tools.helpers import CustomJSONEncoder
from tools.update_no_material import get_no_material_list


# FfprobeScanner(program_id=program_id).ffprobe_scan()

def update_no_material(request):
    try:
        result = get_no_material_list()
        result['title'] = 'Обновление программ со статусом "Нет материала"'
        # result = {'title': 'Обновление программ со статусом "Нет материала"', 'status': 'success',
        #             'message': f"Для программы name обновлена дата эфира с task_sched_date на nearest_sched_date",
        #             'deleted_list': '[deleted_list]', 'old_sched_date': 'task_sched_date', 'new_sched_date': 'nearest_sched_date',
        #             'channel_changed': True,
        #             'old_schedule_id': 'task_sched_id', 'new_schedule_id': 'new_schedule_id',
        #           'sucess_list': ['program_id', 'worker_id', 'file_id', 'file_path'], 'error_list': [10, 9, 8, 7, 6]}
        result = json.loads(json.dumps(result, cls=CustomJSONEncoder))
        request.session['service_report_data'] = result
        return JsonResponse({
            'status': 'success',
            'redirect_url': '/tools/service_report/'
        })
    except Exception as error:
        print(error)
        return JsonResponse({'status': 'error', 'message': str(error)}, status=500)

def service_report(request):
    user_id = request.user.id

    service_report_data = request.session.get('service_report_data')
    return render(request, 'tools/service_report.html',
                  {
                      'service_report_data': service_report_data,
                      'permissions': ask_db_permissions(user_id)
                  })