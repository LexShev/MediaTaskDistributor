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
            # Присоединяемся к персональной группе пользователя
            await self.channel_layer.group_add(
                f"file_manager_user_{self.user.id}",
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
        # Получаем ID пользователя из события
        user_id = event.get('user_id')

        # Отправляем только если это событие для текущего пользователя
        if user_id and self.user and user_id == self.user.id:
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
        elif not user_id and self.user and (self.user.is_staff or self.user.groups.filter(name='admin').exists()):
            # Для админов показываем все обновления
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

    # Отправляем обновление статуса для подсветки кнопки
    async def file_manager_status_update(self, event):
        """Отдельный метод для обновления статуса кнопки в хедере"""
        # Получаем ID пользователя из события
        user_id = event.get('user_id')

        # Отправляем только если это событие для текущего пользователя
        if user_id and self.user and user_id == self.user.id:
            await self.send(text_data=json.dumps({
                "type": "file_manager_status_update",
                "active_count": event.get('active_count', 0),
                "error_count": event.get('error_count', 0),
            }))
        elif not user_id and self.user and (self.user.is_staff or self.user.groups.filter(name='admin').exists()):
            # Для админов показываем все задачи
            await self.send(text_data=json.dumps({
                "type": "file_manager_status_update",
                "active_count": event.get('active_count', 0),
                "error_count": event.get('error_count', 0),
            }))

    async def new_task_created(self, event):
        """Отправка события о новой задаче клиенту с учётом прав доступа"""
        user_id = event.get('user_id')

        # Отправляем только владельцу задачи
        if user_id and self.user and user_id == self.user.id:
            await self.send(text_data=json.dumps({
                "type": "new_task",
                "task_id": event.get('task_id'),
                "celery_task_id": event.get('celery_task_id'),
                "file_name": event.get('file_name'),
                "status": event.get('status'),
                "progress": event.get('progress', 0),
                "speed_mbps": event.get('speed_mbps', 0),
                "transferred_gb": event.get('transferred_gb', 0),
                "file_size_gb": event.get('file_size_gb', 0),
            }))
        # Если owner не указан — показываем админам
        elif not user_id and self.user and (self.user.is_staff or self.user.groups.filter(name='admin').exists()):
            await self.send(text_data=json.dumps({
                "type": "new_task",
                "task_id": event.get('task_id'),
                "celery_task_id": event.get('celery_task_id'),
                "file_name": event.get('file_name'),
                "status": event.get('status'),
                "progress": event.get('progress', 0),
                "speed_mbps": event.get('speed_mbps', 0),
                "transferred_gb": event.get('transferred_gb', 0),
                "file_size_gb": event.get('file_size_gb', 0),
            }))

    @database_sync_to_async
    def get_active_count(self):
        """Возвращает количество активных задач"""
        if self.user.is_staff or self.user.groups.filter(name='admin').exists():
            return FileCopyTask.objects.filter(status__in=['pending', 'copying', 'verifying']).count()
        return FileCopyTask.objects.filter(owner=self.user, status__in=['pending', 'copying', 'verifying']).count()

    @database_sync_to_async
    def get_error_count(self):
        """Возвращает количество задач с ошибками"""
        if self.user.is_staff or self.user.groups.filter(name='admin').exists():
            return FileCopyTask.objects.filter(status='error').count()
        return FileCopyTask.objects.filter(owner=self.user, status='error').count()

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