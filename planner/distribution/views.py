import json
from datetime import datetime, date, timedelta
from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist
from django.core.serializers.json import DjangoJSONEncoder
from django.db import connections
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string

from planner.settings import PLANNER_DB
from .distribution import main_distribution
from .forms import DistributionForm
from .models import Distribution


class CustomJSONEncoder(DjangoJSONEncoder):
    """Кастомный JSON encoder для обработки специальных типов данных"""

    def default(self, obj):
        # Преобразуем datetime в строку
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()

        # Преобразуем timedelta в строку или секунды
        if isinstance(obj, timedelta):
            return str(obj)  # или obj.total_seconds() если нужны секунды

        # Преобразуем Decimal в float
        if isinstance(obj, Decimal):
            return float(obj)

        # Преобразуем bytes в строку (если встречаются бинарные данные)
        if isinstance(obj, bytes):
            return obj.decode('utf-8', errors='ignore')

        # Обработка множеств (set)
        if isinstance(obj, set):
            return list(obj)

        # Обработка генераторов
        if hasattr(obj, '__iter__') and not isinstance(obj, (str, list, dict, tuple)):
            return list(obj)

        # Если объект имеет метод __dict__ (например, модели Django)
        if hasattr(obj, '__dict__'):
            return obj.__dict__

        # Если объект имеет метод to_json или similar
        if hasattr(obj, 'to_json'):
            return obj.to_json()

        # Для любых других объектов пробуем преобразовать в строку
        try:
            return str(obj)
        except Exception as error:
            print(error)
            # Если ничего не помогло, используем родительский метод
            return super().default(obj)

def start_distribution(request):
    user_id = request.user.id
    backup_table = None
    try:
        # Проверяем AJAX запрос
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

        backup_table = create_table_backup("task_list")

        # Парсим JSON данные
        data = json.loads(request.body)
        if not data:
            return JsonResponse({'status': 'error', 'message': 'No data provided'}, status=400)
        distr_sched_end_date = data.get('distr_sched_end_date')
        distr_sched_id = data.get('distr_sched_id')

        try:
            distribution_model = Distribution.objects.get(owner=user_id)
        except ObjectDoesNotExist:
            distribution_model = Distribution(owner=user_id)

            # УСТАНАВЛИВАЕМ ЗНАЧЕНИЯ перед сохранением!
        if distr_sched_end_date:
            distribution_model.distr_sched_end_date = distr_sched_end_date
        if distr_sched_id:
            distribution_model.distr_sched_id = distr_sched_id

        # СОХРАНЯЕМ модель с новыми значениями
        distribution_model.save()

        # Передаем параметры в main_distribution
        result = main_distribution(
            distr_sched_end_date=distr_sched_end_date,
            distr_sched_id=distr_sched_id
        )
        result['title'] = 'Автоматическое распределение задач на отсмотр'
        # Преобразуем данные в JSON-сериализуемый формат
        result = json.loads(json.dumps(result, cls=CustomJSONEncoder))
        request.session['service_report_data'] = result

        cleanup_old_backups("task_list", keep_last=5)
        return JsonResponse({
            'status': 'success',
            'redirect_url': '/tools/service_report/'
        })

    except Exception as error:
        if backup_table:
            mark_backup_as_protected(backup_table)  # Защищаем бэкап
            print(f"Ошибка! Бэкап сохранен как: {backup_table} -> {backup_table}_ERROR")
            print(error)
        return JsonResponse({'status': 'error', 'message': str(error)}, status=500)



def get_distribution_form(request):
    user_id = request.user.id
    try:
        init_dict = Distribution.objects.get(owner=user_id)
    except ObjectDoesNotExist:
        default_distr = Distribution(owner=user_id, distr_sched_end_date=date.today() + timedelta(days=1))
        default_distr.save()
        init_dict = Distribution.objects.get(owner=user_id)
        print("Новые Distribution настройки созданы")

    if request.method == 'GET':
        distribution_form = DistributionForm(instance=init_dict)
        form_html = render_to_string('distribution/distribution_form.html', {'distribution_form': distribution_form})
        return HttpResponse(form_html)
    return HttpResponse('')


def create_table_backup(table_name, backup_suffix=None):
    """Создает бэкап таблицы с версией"""
    if not backup_suffix:
        backup_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")

    backup_table_name = f"{table_name}_backup_{backup_suffix}"

    with connections[PLANNER_DB].cursor() as cursor:
        # Создаем копию таблицы
        cursor.execute(f"SELECT * INTO {backup_table_name} FROM {table_name}")

    return backup_table_name


def mark_backup_as_protected(backup_table_name):
    """Переименовывает бэкап, чтобы защитить его от удаления"""
    protected_name = f"{backup_table_name}_ERROR"

    with connections[PLANNER_DB].cursor() as cursor:
        try:
            cursor.execute(f"EXEC sp_rename '{backup_table_name}', '{protected_name}'")
            print(f"Бэкап защищен: {backup_table_name} -> {protected_name}")
        except Exception as e:
            print(f"Ошибка переименования бэкапа: {e}")

def cleanup_old_backups(table_name, keep_last=5):
    """Удаляет старые бэкапы, оставляя только keep_last последних"""
    with connections[PLANNER_DB].cursor() as cursor:
        cursor.execute(f"""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME LIKE '{table_name}_backup_%'
            AND TABLE_NAME NOT LIKE '%_ERROR'
            ORDER BY TABLE_NAME DESC
        """)
        backups = [row[0] for row in cursor.fetchall()]

        # Удаляем старые бэкапы
        for backup in backups[keep_last:]:
            cursor.execute(f"DROP TABLE {backup}")

