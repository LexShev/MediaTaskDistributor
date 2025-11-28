from django.utils import timezone
import pytz
from .models import DailyWorkTime, UserActivity


class WorkTimeTrackingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.moscow_tz = pytz.timezone('Europe/Moscow')

    def __call__(self, request):
        if (request.user.is_authenticated and
                not request.path.startswith('/admin/') and
                not request.path.startswith('/static/') and
                not request.path.startswith('/api/')):
            self.track_user_activity(request)

        response = self.get_response(request)
        return response

    def track_user_activity(self, request):
        user = request.user

        # ПРИНУДИТЕЛЬНО создаем время с +03:00
        now_utc = timezone.now()
        now_moscow = now_utc.astimezone(self.moscow_tz)
        today = now_moscow.date()

        # 1. Записываем активность с ПРИНУДИТЕЛЬНЫМ временем
        UserActivity.objects.create(
            user=user,
            path=request.path,
            timestamp=now_moscow  # Явно устанавливаем время!
        )

        # 2. Создаем/обновляем запись рабочего времени с ПРИНУДИТЕЛЬНЫМ временем
        daily_record, created = DailyWorkTime.objects.get_or_create(
            user=user,
            date=today,
            defaults={
                'first_request': now_moscow,  # Московское время!
                'last_request': now_moscow,
                'total_requests': 1
            }
        )

        if not created:
            daily_record.last_request = now_moscow
            daily_record.total_requests += 1
            daily_record.save()