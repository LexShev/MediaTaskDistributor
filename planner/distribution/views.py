import json
import threading
from datetime import datetime, date, timedelta
from decimal import Decimal

from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string

from .distribution import main_distribution
from .forms import DistributionForm


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
    try:
        # Проверяем AJAX запрос
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

        # Парсим JSON данные
        data = json.loads(request.body)
        if not data:
            return JsonResponse({'status': 'error', 'message': 'No data provided'}, status=400)
        distr_sched_end_date = data.get('distr_sched_end_date')
        distr_sched_id = data.get('distr_sched_id')

        distribution_form = DistributionForm(data)
        if distribution_form.is_valid():
            distribution_form.save()

        # Передаем параметры в main_distribution
        result = {}
        result = main_distribution(
            distr_sched_end_date=distr_sched_end_date,
            distr_sched_id=distr_sched_id
        )

        result['title'] = 'Автоматическое распределение задач на отсмотр'
        # Преобразуем данные в JSON-сериализуемый формат
        result = json.loads(json.dumps(result, cls=CustomJSONEncoder))
        request.session['service_report_data'] = result
        print('DISTR', distr_sched_end_date, type(distr_sched_end_date), distr_sched_id, type(distr_sched_id))
        return JsonResponse({
            'status': 'success',
            'redirect_url': '/tools/service_report/'
        })

    except Exception as error:
        print(error)
        return JsonResponse({'status': 'error', 'message': str(error)}, status=500)



def get_distribution_form(request):
    if request.method == 'GET':
        distribution_form = DistributionForm()
        form_html = render_to_string('distribution/distribution_form.html', {'distribution_form': distribution_form})
        return HttpResponse(form_html)
    return HttpResponse('')



