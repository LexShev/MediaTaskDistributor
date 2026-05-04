# planner/file_manager/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import FileCopyTask


class FileManagerConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer для обновлений file manager"""

    async def connect(self):
        """Подключение к WebSocket"""
        self.user = self.scope.get("user")

        if self.user and self.user.is_authenticated:
            # Присоединяемся к группе обновлений
            await self.channel_layer.group_add(
                "file_manager_updates",
                self.channel_name
            )
            await self.accept()

            # Отправляем подтверждение подключения
            await self.send(text_data=json.dumps({
                "type": "connection_established",
                "message": "Connected to File Manager WebSocket"
            }))
        else:
            await self.close(code=4001)

    async def disconnect(self, close_code):
        """Отключение от WebSocket"""
        await self.channel_layer.group_discard(
            "file_manager_updates",
            self.channel_name
        )

    async def receive(self, text_data):
        """Получение сообщения от клиента"""
        try:
            data = json.loads(text_data)
            action = data.get('action')

            if action == 'request_update':
                # Клиент запрашивает обновление всех задач
                tasks = await self.get_active_tasks()
                await self.send(text_data=json.dumps({
                    "type": "full_update",
                    "tasks": tasks
                }))

        except json.JSONDecodeError:
            pass

    async def file_progress_update(self, event):
        """Отправка обновления прогресса клиенту"""
        await self.send(text_data=json.dumps({
            "type": "progress_update",
            "task_id": event.get('task_id'),
            "celery_task_id": event.get('celery_task_id'),
            "status": event.get('status'),
            "progress": event.get('progress'),
            "speed_mbps": event.get('speed_mbps'),
            'file_size_gb': event.get('file_size_gb'),
            "transferred_gb": event.get('transferred_gb'),
            "error_message": event.get('error_message'),
        }))

    @database_sync_to_async
    def get_active_tasks(self):
        """Получает активные задачи из БД"""
        if self.user.is_staff or self.user.groups.filter(name='admin').exists():
            tasks = FileCopyTask.objects.filter(status__in=['pending', 'copying', 'verifying'])
        else:
            tasks = FileCopyTask.objects.filter(
                owner=self.user,
                status__in=['pending', 'copying', 'verifying']
            )

        return [{
            'id': task.id,
            'celery_task_id': task.celery_task_id,
            'file_name': task.file_name,
            'status': task.status,
            'progress': task.progress,
            'speed_mbps': task.speed_mbps,
            'transferred_gb': task.transferred_gb,
            'file_size_gb': task.file_size_gb,
        } for task in tasks]