import json
from django.http import JsonResponse
from django.utils import timezone

from notifications.models import NotificationRecipient
from notifications.notification_services import create_notification


def notification_create(request):
    # Создание уведомления при каком-то действии
    user_id = request.user.id
    try:
        employee_ids = json.loads(request.body)
        if not employee_ids:
            return JsonResponse({'status': 'error', 'message': 'message'})
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

def mark_notification_as_read(request):
    user_id = request.user.id
    try:
        read_ids = json.loads(request.body)
        if not read_ids:
            return JsonResponse({'status': 'error', 'message': 'No data provided'})

        updated_count = NotificationRecipient.objects.filter(
            id__in=read_ids,
            recipient_id=user_id,
        ).update(
            is_read=True,
            read_at=timezone.now()
        )

        return JsonResponse({
            'status': 'success',
            'message': f'Успешно прочитано {updated_count} уведомлений',
            'updated_count': updated_count
        })
    except Exception as error:
        print(error)
        return JsonResponse({'status': 'error', 'message': str(error)})
