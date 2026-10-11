"""Роли модуля перспективных сеток.

Навигация в хэдер не добавляется; доступ проверяется внутри вьюх по id групп.
- senior_editor (9) — правит сетку;
- chief_editor (8)  — просмотр + утверждение;
- editors (6)       — только просмотр.
"""

from schedule_perspective import constants

ROLE_SENIOR = 'senior_editor'
ROLE_CHIEF = 'chief_editor'
ROLE_EDITOR = 'editors'


def get_role(user):
    if not user or not user.is_authenticated:
        return None
    ids = set(user.groups.values_list('id', flat=True))
    if constants.SENIOR_EDITOR_GROUP_ID in ids:
        return ROLE_SENIOR
    if constants.CHIEF_EDITOR_GROUP_ID in ids:
        return ROLE_CHIEF
    if constants.EDITORS_GROUP_ID in ids:
        return ROLE_EDITOR
    return None


def can_view(user):
    return get_role(user) is not None


def can_edit(user):
    return get_role(user) == ROLE_SENIOR


def can_approve(user):
    return get_role(user) == ROLE_SENIOR
