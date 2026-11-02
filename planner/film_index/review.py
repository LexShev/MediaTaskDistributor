"""Бизнес-логика ручного разбора сопоставления."""

from film_index import normalization, repository


def _program_id(value):
    try:
        value = int(value)
    except (TypeError, ValueError):
        return None
    return value if value > 0 else None


def _kinopoisk_id(value):
    kp_id = normalization.parse_kinopoisk_id(value)
    if kp_id is None or not (1 <= kp_id <= normalization.MAX_KP_ID):
        return None
    return kp_id


def _locked_result(program_id, user_id):
    """Возвращает ошибку, если карточку сейчас решает другой редактор."""
    lock = repository.get_review_lock(program_id)
    if lock and lock['editor_id'] != user_id:
        return {
            'status': 'locked',
            'message': f'Материал занят {lock["editor_name"]}',
            'editor_id': lock['editor_id'],
            'editor_name': lock['editor_name'],
        }
    return None


def resolve(program_id, kp_id, user_id) -> dict:
    program_id = _program_id(program_id)
    kp_id = _kinopoisk_id(kp_id)
    if not program_id or not kp_id:
        return {'status': 'error', 'message': 'Некорректный program_id или kinopoisk_id'}
    locked = _locked_result(program_id, user_id)
    if locked:
        return locked
    repository.apply_manual_match(program_id, kp_id)
    repository.resolve_review(program_id, kp_id, user_id)
    repository.release_review_lock(program_id, user_id)
    return {'status': 'success', 'message': 'Сопоставление сохранено'}


def reject(program_id, user_id) -> dict:
    program_id = _program_id(program_id)
    if not program_id:
        return {'status': 'error', 'message': 'Некорректный program_id'}
    locked = _locked_result(program_id, user_id)
    if locked:
        return locked
    repository.clear_manual_match(program_id)
    repository.reject_review(program_id, user_id)
    repository.release_review_lock(program_id, user_id)
    return {'status': 'success', 'message': 'Помечено как «не найден»'}


def revert(program_id, user_id) -> dict:
    program_id = _program_id(program_id)
    if not program_id:
        return {'status': 'error', 'message': 'Некорректный program_id'}
    locked = _locked_result(program_id, user_id)
    if locked:
        return locked
    repository.clear_manual_match(program_id)
    repository.revert_review(program_id)
    repository.release_review_lock(program_id, user_id)
    return {'status': 'success', 'message': 'Возвращено в очередь'}
