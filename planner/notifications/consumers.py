import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from django.utils import timezone

from .models import Notification, NotificationRecipient

logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        logger.info(f"USER: {self.user}, AUTH: {self.user.is_authenticated}")

        if self.user.is_authenticated:
            self.group_name = f'user_{self.user.id}'

            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )

            await self.accept()
            logger.info(f"WebSocket connected for user {self.user.id}")

            # Отправляем непрочитанные уведомления при подключении
            await self.send_pending_notifications()
        else:
            logger.warning("Rejected WebSocket connection for unauthenticated user")
            await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
            logger.info(f"WebSocket disconnected for user {getattr(self.user, 'id', 'unknown')}")

    async def receive(self, text_data):
        """Обработка сообщений от клиента"""
        try:
            data = json.loads(text_data)
            action = data.get('action')

            if action == 'mark_as_read':
                await self.mark_notification_as_read(data.get('notification_id'))
            elif action == 'mark_as_displayed':
                await self.mark_notification_as_displayed(data.get('notification_id'))
            elif action == 'mark_all_as_read':
                await self.mark_all_as_read()

        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    async def send_notification(self, event):
        """Отправка уведомления клиенту"""
        try:
            logger.info(f"Sending notification to client: {event['notification']}")
            await self.send(text_data=json.dumps({
                'type': 'notification',
                'notification': event['notification']
            }))
        except Exception as e:
            logger.error(f"Error sending notification: {e}")

    @database_sync_to_async
    def get_pending_notifications(self):
        pending = NotificationRecipient.objects.filter(
            recipient=self.user,
            is_displayed=False
        ).select_related('notification').order_by('-notification__timestamp')[:10]

        result = []

        for recipient_link in pending:
            notification = recipient_link.notification

            result.append({
                'id': notification.notice_id,
                'recipient_id': recipient_link.id,
                'message': notification.message,
                'comment': notification.comment or '',
                'type': notification.notification_type,
                'timestamp': notification.timestamp.isoformat(),
                'sender': notification.sender.username if notification.sender else 'System',
            })

        return result

    async def send_pending_notifications(self):
        try:
            pending = await self.get_pending_notifications()

            for notification in pending:
                await self.send(text_data=json.dumps({
                    'type': 'notification',
                    'notification': notification
                }))

        except Exception as e:
            logger.error(f"Error sending pending notifications: {e}")

    @database_sync_to_async
    def mark_notification_as_displayed(self, notification_id):
        """Отметить уведомление как показанное"""
        try:
            # Ищем в NotificationRecipient!
            NotificationRecipient.objects.filter(
                id=notification_id,
                recipient=self.user
            ).update(
                is_displayed=True,
                displayed_at=timezone.now()
            )
            logger.info(f"Marked notification {notification_id} as displayed")
        except Exception as e:
            logger.error(f"Error marking notification as displayed: {e}")

    @database_sync_to_async
    def mark_notification_as_read(self, notification_id):
        """Отметить уведомление как прочитанное"""
        try:
            # Ищем в NotificationRecipient
            NotificationRecipient.objects.filter(
                id=notification_id,
                recipient=self.user
            ).update(
                is_read=True,
                is_displayed=True,
                read_at=timezone.now()
            )
            logger.info(f"Marked notification {notification_id} as read")
        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")

    @database_sync_to_async
    def mark_all_as_read(self):
        """Отметить все уведомления как прочитанные"""
        try:
            NotificationRecipient.objects.filter(
                recipient=self.user,
                is_read=False
            ).update(
                is_read=True,
                read_at=timezone.now()
            )
            logger.info(f"Marked all notifications as read for user {self.user.id}")
        except Exception as e:
            logger.error(f"Error marking all as read: {e}")