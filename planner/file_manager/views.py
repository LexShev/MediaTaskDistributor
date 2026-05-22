# planner/file_manager/views.py
import json
from django.shortcuts import render
from django.http import JsonResponse
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from django.template.loader import render_to_string
from django.utils import timezone

from main.permission_pannel import ask_db_permissions
from main.settings.main_settings import get_main_settings
from .models import FileCopyTask
from tools.tasks import copy_large_file


@login_required
def file_manager(request):
    """Главная страница file manager"""
    user = request.user
    user_id = request.user.id
    user_group = request.user.groups.first().id
    context = {
        'is_admin': user.is_staff or user.groups.filter(name='admin').exists(),
        'permissions': ask_db_permissions(user_id),
        'tabs': get_main_settings().get_header_panels(user_group)
    }
    return render(request, 'file_manager/file_manager.html', context)


@login_required
@require_http_methods(["POST"])
def load_file_manager(request):
    """Загрузка списка задач с фильтрацией и пагинацией"""
    try:
        user = request.user

        is_admin = user.is_staff or user.groups.filter(name='admin').exists()

        # Получаем параметры из запроса
        data = json.loads(request.body)
        page_number = data.get('page_number', 1)
        search_input = data.get('search_input', '').strip()
        status_filter = data.get('status_filter')

        # Базовый queryset
        if is_admin:
            tasks = FileCopyTask.objects.all()
        else:
            tasks = FileCopyTask.objects.filter(owner=user)

        # Фильтрация
        filters = Q()

        if search_input:
            filters &= Q(file_name__icontains=search_input) | Q(file_path__icontains=search_input)

        if status_filter:
            filters &= Q(status=status_filter)

        if filters:
            tasks = tasks.filter(filters)

        # Сортировка
        tasks = tasks.order_by('-created_at')

        # Пагинация
        paginator = Paginator(tasks, 16)

        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        # Рендерим HTML таблицы
        html = render_to_string(
            'file_manager/file_manager_list.html',
            {
                'tasks': page_obj,
                'page_obj': page_obj,
                'paginator': paginator,
                'is_admin': is_admin,
                'total_count': tasks.count(),
                'start_number': paginator.count - page_obj.start_index() + 1
            },
            request=request
        )

        return JsonResponse({
            'status': 'success',
            'html': html,
            'active_tasks_count': tasks.filter(status__in=['pending', 'copying', 'verifying']).count()
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def retry_file_copy(request):
    """Повторная отправка задачи на копирование"""
    try:
        data = json.loads(request.body)
        task_id = data.get('task_id')

        if not task_id:
            return JsonResponse({'status': 'error', 'message': 'Task ID is required'}, status=400)

        # Получаем задачу
        try:
            task = FileCopyTask.objects.get(id=task_id)
        except FileCopyTask.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Task not found'}, status=404)

        # Проверяем права
        user = request.user
        is_admin = user.is_staff or user.groups.filter(name='admin').exists()

        if not is_admin and task.owner != user:
            return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)

        # Проверяем, можно ли повторить
        if not task.can_retry:
            return JsonResponse({'status': 'error', 'message': 'Task cannot be retried'}, status=400)

        # Создаем новую задачу
        new_task = copy_large_file.apply_async(
            args=(task.file_path, task.destination_path),
            kwargs={'file_id': task.file_id, 'user_id': request.user.id,'priority': task.priority},
            queue='file_copy'
        )

        # Создаем запись в БД
        FileCopyTask.objects.create(
            owner=user,
            celery_task_id=new_task.id,
            file_id=task.file_id,
            file_path=task.file_path,
            file_name=task.file_name,
            destination_path=task.destination_path,
            status='pending',
            priority=task.priority,
            retry_count=task.retry_count + 1,
            comment=f'Retry from task #{task.id}'
        )

        return JsonResponse({
            'status': 'success',
            'message': f'Task {new_task.id} created for retry',
            'task_id': new_task.id
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def cancel_copy_task(request):
    """Отмена активной задачи копирования"""
    try:
        data = json.loads(request.body)
        task_id = data.get('task_id')

        if not task_id:
            return JsonResponse({'status': 'error', 'message': 'Task ID is required'}, status=400)

        task = FileCopyTask.objects.get(id=task_id)

        # Проверяем, активна ли задача
        if not task.is_active:
            return JsonResponse({'status': 'error', 'message': 'Task is not active'}, status=400)

        # Отменяем Celery задачу если есть
        if task.celery_task_id:
            from celery import current_app
            current_app.control.revoke(task.celery_task_id, terminate=True)

        # Обновляем статус
        task.status = 'error'
        task.comment = 'Task cancelled by user'
        task.completed_at = timezone.now()
        task.save()

        return JsonResponse({'status': 'success', 'message': 'Task cancelled'})

    except FileCopyTask.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Task not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
def active_task_count(request):
    """Возвращает количество активных задач и задач с ошибками"""
    user = request.user

    if user.is_staff or user.groups.filter(name='admin').exists():
        active_tasks = FileCopyTask.objects.filter(
            status__in=['pending', 'copying', 'verifying']
        )
        error_tasks = FileCopyTask.objects.filter(
            status='error'
        )
    else:
        active_tasks = FileCopyTask.objects.filter(
            owner=user,
            status__in=['pending', 'copying', 'verifying']
        )
        error_tasks = FileCopyTask.objects.filter(
            owner=user,
            status='error'
        )

    return JsonResponse({
        'status': 'success',
        'active_count': active_tasks.count(),
        'error_count': error_tasks.count()
    })