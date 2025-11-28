from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta


class DailyWorkTime(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='work_times')
    date = models.DateField()  # Конкретная дата
    first_request = models.DateTimeField()  # Первый запрос дня
    last_request = models.DateTimeField()  # Последний запрос дня
    total_requests = models.PositiveIntegerField(default=0)  # Количество запросов за день

    class Meta:
        unique_together = ['user', 'date']  # Одна запись на пользователя в день
        ordering = ['-date']

    @property
    def start_time(self):
        """Время начала в формате HH:MM"""
        return self.first_request.strftime('%H:%M')

    @property
    def end_time(self):
        """Время окончания в формате HH:MM"""
        return self.last_request.strftime('%H:%M')

    @property
    def work_duration(self) -> timedelta | None:
        """Общее время работы за день"""
        if self.first_request and self.last_request:
            return self.last_request - self.first_request
        return None

    @property
    def work_duration_hours(self) -> float:
        """Общее время работы в часах"""
        duration = self.work_duration
        if duration:
            return round(duration.total_seconds() / 3600, 2)
        return 0.0

    @property
    def last_request_msk(self):
        """Последнее обращение в московском времени"""
        from django.utils import timezone
        return timezone.localtime(self.last_request)

    def __str__(self):
        return f"{self.user.username} - {self.date}"


class UserActivity(models.Model):
    """Дополнительная таблица для детального отслеживания активности"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    timestamp = models.DateTimeField(auto_now_add=True)
    path = models.CharField(max_length=500)  # URL запроса

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'User Activity'
        verbose_name_plural = 'User Activities'

    def __str__(self):
        return f"{self.user.username} - {self.timestamp}"