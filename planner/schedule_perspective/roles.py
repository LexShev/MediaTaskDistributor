"""Роли модуля перспективных сеток.

Навигация в хэдер не добавляется; доступ проверяется внутри вью по именам групп.
- senior_editor — правит сетку;
- chief_editor  — просмотр + утверждение;
- editors       — только просмотр;
- admin         — просмотр + правка.
"""

ROLE_SENIOR = 'senior_editor'
ROLE_CHIEF = 'chief_editor'
ROLE_EDITOR = 'editors'
ROLE_ADMIN = 'admin'

EDIT_ROLES = {ROLE_ADMIN, ROLE_SENIOR, ROLE_CHIEF}


def get_roles(user):
    if not user or not user.is_authenticated:
        return set()
    return set(user.groups.values_list('name', flat=True))


def can_view(user):
    return bool(get_roles(user))


def can_edit(user):
    return bool(get_roles(user) & EDIT_ROLES)


def can_approve(user):
    return bool(get_roles(user) & EDIT_ROLES)
