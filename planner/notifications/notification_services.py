from django.contrib.auth.models import User
from .models import Notification, NotificationRecipient
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from main.form_choices import get_choice


def create_notification(sender, recipients, message, comment='', notification_type='info', schedule_id=None):
    """
    Создание уведомления для одного или нескольких получателей

    Args:
        sender: User object or None
        recipients: User object, list of User objects, or list of user IDs
        message: str
        comment: str (optional)
        notification_type: str (info, success, warning, error)
    """
    # Валидация типа уведомления
    valid_types = dict(get_choice().notification_type())
    if notification_type not in valid_types:
        notification_type = 'info'

    # Создаем само уведомление
    notification = Notification.objects.create(
        sender=sender if isinstance(sender, User) else None,
        message=message,
        comment=comment,
        notification_type=notification_type,
        schedule_id=schedule_id
    )

    # Определяем получателей
    if isinstance(recipients, User):
        recipients_list = [recipients]
    elif isinstance(recipients, (list, tuple)):
        recipients_list = []
        for r in recipients:
            if isinstance(r, User):
                recipients_list.append(r)
            else:
                try:
                    recipients_list.append(User.objects.get(id=r))
                except User.DoesNotExist:
                    continue
    else:
        recipients_list = []

    # Создаем связи получателей и отправляем через WebSocket
    channel_layer = get_channel_layer()

    for recipient in recipients_list:
        recipient_link = NotificationRecipient.objects.create(
            notification=notification,
            recipient=recipient,
            is_read=False,
            is_displayed=False
        )

        # Отправка через WebSocket
        async_to_sync(channel_layer.group_send)(
            f'user_{recipient.id}',
            {
                'type': 'send_notification',
                'notification': {
                    'id': notification.notice_id,
                    'recipient_id': recipient_link.id,
                    'message': message,
                    'comment': comment,
                    'type': notification_type,
                    'timestamp': notification.timestamp.isoformat(),
                    'sender': sender.username if sender else 'System'
                }
            }
        )

    return notification
