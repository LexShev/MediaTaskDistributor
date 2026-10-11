"""Конечный автомат статусов дня и (лог-)уведомления.

draft -> chief_approved -> final_approved; переоткрытие любого -> draft.
Пока уведомления только пишутся в лог (реальную отправку не делаем).
"""

from schedule_perspective import constants, repositories


def approve(schedule_id, dates, user_id):
    """draft -> chief_approved."""
    return _transition(schedule_id, dates, constants.STATUS_CHIEF_APPROVED,
                       user_id, log_message='Тестовое уведомление редактору отправлено')


def finalize(schedule_id, dates, user_id):
    """chief_approved -> final_approved."""
    return _transition(schedule_id, dates, constants.STATUS_FINAL_APPROVED, user_id)


def reopen(schedule_id, dates, user_id):
    """любой -> draft."""
    return _transition(schedule_id, dates, constants.STATUS_DRAFT, user_id,
                       log_message='Тестовое уведомление редактору отправлено')


def _transition(schedule_id, dates, status, user_id, log_message=None):
    if not dates:
        return {'status': 'error', 'message': 'Не выбран период'}
    updated = repositories.set_status(schedule_id, dates, status, user_id)
    if log_message:
        print(log_message)
    return {
        'status': 'success',
        'message': f'Обновлено дней: {updated}',
        'updated': updated,
    }
