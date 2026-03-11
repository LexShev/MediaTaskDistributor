import json
from django.http import JsonResponse
from notifications.notification_services import create_notification


def notification_create(request):
    # Создание уведомления при каком-то действии
    user_id = request.user.id
    try:
        employee_ids = json.loads(request.body)
        if not employee_ids:
            return JsonResponse({'status': 'error', 'message': 'message'})
        print('employee_ids', employee_ids, type(employee_ids))
        create_notification(
            sender=request.user,
            recipients=employee_ids,  # можно передать список ID
            message="Новая задача после исправлений",
            comment="Требуется ваше участие",
            notification_type="info"
        )

        message = 'Успешно отправлено'
        return JsonResponse({'status': 'success', 'message': message})

    except Exception as error:
        print(error)
        return JsonResponse({'status': 'error', 'message': str(error)})
