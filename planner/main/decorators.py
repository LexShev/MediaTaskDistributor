from functools import wraps

from django.http import JsonResponse


def ajax_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse(
                {'status': 'auth_error', 'message': 'Сессия истекла. Войдите снова.'},
                status=401,
            )
        return view_func(request, *args, **kwargs)

    return wrapper
