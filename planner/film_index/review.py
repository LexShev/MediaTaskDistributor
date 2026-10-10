"""Бизнес-логика ручного разбора сопоставления."""

from film_index import repository


def resolve(program_id, kp_id, user_id) -> dict:
    if not program_id or not kp_id:
        return {'status': 'error', 'message': 'Не указан program_id или kinopoisk_id'}
    repository.apply_manual_match(program_id, kp_id)
    repository.resolve_review(program_id, kp_id, user_id)
    return {'status': 'success', 'message': 'Сопоставление сохранено'}


def reject(program_id, user_id) -> dict:
    if not program_id:
        return {'status': 'error', 'message': 'Не указан program_id'}
    repository.clear_manual_match(program_id)
    repository.reject_review(program_id, user_id)
    return {'status': 'success', 'message': 'Помечено как «не найден»'}


def revert(program_id) -> dict:
    if not program_id:
        return {'status': 'error', 'message': 'Не указан program_id'}
    repository.clear_manual_match(program_id)
    repository.revert_review(program_id)
    return {'status': 'success', 'message': 'Возвращено в очередь'}
