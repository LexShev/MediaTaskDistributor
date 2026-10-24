"""Конечный автомат статусов дня и уведомления о смене статуса.

draft -> chief_approved -> final_approved; переоткрытие любого -> draft.
При каждой смене статуса отправляется уведомление (пока только админу).
"""

from django.contrib.auth.models import User

from notifications.notification_services import create_notification
from schedule_perspective import constants, repositories

# Получатели уведомлений (id пользователей). Пока только админ.
NOTIFY_RECIPIENT_IDS = (1, 28)

_STATUS_LABELS = {
    constants.STATUS_CHIEF_APPROVED: 'утверждён',
    constants.STATUS_FINAL_APPROVED: 'финализирован',
    constants.STATUS_DRAFT: 'переоткрыт',
}

_STATUS_TYPES = {
    constants.STATUS_CHIEF_APPROVED: 'success',
    constants.STATUS_FINAL_APPROVED: 'success',
    constants.STATUS_DRAFT: 'warning',
}


def approve(schedule_id, dates, user_id):
    """draft -> chief_approved."""
    return _transition(schedule_id, dates, constants.STATUS_CHIEF_APPROVED, user_id)


def finalize(schedule_id, dates, user_id):
    """chief_approved -> final_approved."""
    return _transition(schedule_id, dates, constants.STATUS_FINAL_APPROVED, user_id)


def reopen(schedule_id, dates, user_id):
    """любой -> draft."""
    return _transition(schedule_id, dates, constants.STATUS_DRAFT, user_id)


def _transition(schedule_id, dates, status, user_id):
    if not dates:
        return {'status': 'error', 'message': 'Не выбран период'}
    updated = repositories.set_status(schedule_id, dates, status, user_id)
    _notify_status_change(schedule_id, dates, status, user_id)
    return {
        'status': 'success',
        'message': f'Обновлено дней: {updated}',
        'updated': updated,
    }


def _format_period(dates):
    ordered = sorted(dates)
    first, last = ordered[0], ordered[-1]
    if first == last:
        return f'{first:%d.%m.%Y}'
    return f'{first:%d.%m.%Y} – {last:%d.%m.%Y}'


def _notify_status_change(schedule_id, dates, status, user_id):
    """Уведомление о смене статуса: канал + изменённый период."""
    channel = constants.CHANNELS.get(schedule_id, str(schedule_id))
    sender = User.objects.filter(id=user_id).first()
    label = _STATUS_LABELS.get(status, status)
    try:
        create_notification(
            sender=sender,
            recipients=list(NOTIFY_RECIPIENT_IDS),
            message=f'Сетка «{channel}»: {_format_period(dates)} — статус {label}',
            comment=f'Статус изменил: {sender.username if sender else user_id}',
            notification_type=_STATUS_TYPES.get(status, 'info'),
            schedule_id=schedule_id,
        )
    except Exception as error:  # уведомление не должно ломать смену статуса
        print(f'Не удалось отправить уведомление о статусе: {error}')
