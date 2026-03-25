from django.db import models
from django.contrib.auth.models import User

from main.form_choices import choice


class Notification(models.Model):
    notice_id = models.AutoField(primary_key=True)
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='sent_notifications')
    message = models.TextField()
    comment = models.TextField(blank=True, null=True)
    notification_type = models.CharField(max_length=20, choices=choice.notification_type, default='info')
    schedule_id = models.IntegerField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    # Для массовых рассылок - храним список получателей
    recipients = models.ManyToManyField(User, through='NotificationRecipient')

    class Meta:
        ordering = ['-timestamp']


class NotificationRecipient(models.Model):
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)
    is_displayed = models.BooleanField(default=False)  # Показывалось ли уведомление
    displayed_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('notification', 'recipient')
        indexes = [
            models.Index(fields=['recipient', 'is_displayed']),
            models.Index(fields=['recipient', 'is_read']),
        ]