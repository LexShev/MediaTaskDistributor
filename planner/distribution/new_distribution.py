import random
from datetime import date, datetime, timedelta
from typing import Dict, List

from django.db import connections

from planner.settings import OPLAN_DB, PLANNER_DB

DEFAULT_PROGRAM_TYPES = (4, 5, 6, 10, 11, 12, 16)
DEFAULT_SCHEDULES_IDS = (3, 5, 6, 7, 8, 9, 10, 11, 12, 20)


def main_distribution(distr_sched_end_date=None, distr_sched_id=None, remake_percent=20) -> Dict[str, str]:
    start_work_date = date.today()
    start_distribution_date = date.today() + timedelta(days=1)
    if distr_sched_end_date:
        distr_sched_end_date = check_date(distr_sched_end_date)
    else:
        distr_sched_end_date = date.today()

    work_duration = (distr_sched_end_date - start_work_date).days
    print('Будет обработано', work_duration, 'дней')

    if distr_sched_id:
        distr_sched_id = (distr_sched_id,)
    else:
        distr_sched_id = DEFAULT_SCHEDULES_IDS

    # Получаем все задачи
    material_list = oplan_material_list_with_remake(
        start_date=start_work_date,
        schedules_id=distr_sched_id,
        work_duration=work_duration
    )

    if not material_list:
        return {'status': 'success', 'message': 'Нет новых задач для распределения',
                'success_list': [], 'error_list': []}

    success_list = []
    error_list = []

    distribution_plan = create_distribution_plan(material_list, start_distribution_date, remake_percent)

    for day in distribution_plan:
        day_stats = calculate_day_stats(day, day['work_date'])
        day.update(day_stats)

    return {'status': 'success', 'message': 'Распределение успешно завершено без ошибок',
            'success_list': success_list, 'error_list': error_list, 'distribution_plan': distribution_plan}


def calculate_day_stats(day_plan, work_date):
    """Рассчитывает статистику по задачам за день"""
    regular_duration = 0
    remake_duration = 0
    regular_count = 0
    remake_count = 0
    worker_stats = {}  # Статистика по сотрудникам

    # Получаем ранее распределенные задачи из БД
    existing_loads = get_real_daily_load(work_date)

    for task in day_plan['tasks']:
        duration = task.get('Progs_duration', 0)
        worker_id = task.get('worker_id')
        is_remake = task.get('is_remake', False)

        # Общая статистика
        if is_remake:
            remake_duration += duration
            remake_count += 1
        else:
            regular_duration += duration
            regular_count += 1

        # Статистика по сотрудникам
        if worker_id not in worker_stats:
            # Инициализируем с данными о ранее распределенных задачах
            existing_duration = existing_loads.get(worker_id, 0)
            existing_tasks = 0  # Можно добавить подсчет задач если нужно
            worker_stats[worker_id] = {
                'total_duration': existing_duration,
                'task_count': existing_tasks,
                'existing_duration': existing_duration,  # Ранее распределенные
                'existing_tasks': existing_tasks,  # Ранее распределенные
                'new_duration': 0,  # Новые в этом распределении
                'new_tasks': 0,  # Новые в этом распределении
                'remake_duration': 0,
                'regular_duration': 0,
                'remake_count': 0,
                'regular_count': 0
            }

        # Добавляем новые задачи к существующей нагрузке
        worker_stats[worker_id]['total_duration'] += duration
        worker_stats[worker_id]['new_duration'] += duration
        worker_stats[worker_id]['new_tasks'] += 1
        worker_stats[worker_id]['task_count'] += 1

        if is_remake:
            worker_stats[worker_id]['remake_duration'] += duration
            worker_stats[worker_id]['remake_count'] += 1
        else:
            worker_stats[worker_id]['regular_duration'] += duration
            worker_stats[worker_id]['regular_count'] += 1

    total_tasks = regular_count + remake_count
    total_duration = regular_duration + remake_duration

    # Рассчитываем проценты
    regular_percentage = (regular_count / total_tasks * 100) if total_tasks > 0 else 0
    remake_percentage = (remake_count / total_tasks * 100) if total_tasks > 0 else 0

    return {
        'regular_duration': regular_duration,
        'remake_duration': remake_duration,
        'regular_count': regular_count,
        'remake_count': remake_count,
        'total_tasks': total_tasks,
        'regular_percentage': regular_percentage,
        'remake_percentage': remake_percentage,
        'worker_stats': worker_stats
    }

def oplan_material_list_with_remake(start_date, work_duration, program_type=DEFAULT_PROGRAM_TYPES,
                                    schedules_id=DEFAULT_SCHEDULES_IDS) -> List[dict]:
    columns = [
        ('Progs', 'program_id'), ('Progs', 'parent_id'), ('SchedDay', 'schedule_id'), ('Progs', 'program_type_id'),
        ('Progs', 'name'), ('Progs', 'production_year'), ('Progs', 'AnonsCaption'), ('Progs', 'episode_num'),
        ('Progs', 'duration'), ('Progs', 'SuitableMaterialForScheduleID'), ('SchedDay', 'day_date'),
        ('SchedProg', 'DateTime')
    ]
    material_list = []

    with connections[OPLAN_DB].cursor() as cursor:
        sql_columns = ', '.join([f'{col}.[{val}]' for col, val in columns])
        django_columns = [f'{col}_{val}' for col, val in columns]

        # Запрос для обычных задач (никогда не деланных)
        try:
            new_tasks_query = f'''
                SELECT DISTINCT {sql_columns}
                FROM [{OPLAN_DB}].[dbo].[program] AS Progs
                JOIN [{OPLAN_DB}].[dbo].[scheduled_program] AS SchedProg
                    ON Progs.[program_id] = SchedProg.[program_id]
                JOIN [{OPLAN_DB}].[dbo].[schedule_day] AS SchedDay
                    ON SchedProg.[schedule_day_id] = SchedDay.[schedule_day_id]
                LEFT JOIN [{PLANNER_DB}].[dbo].[task_list] AS Task
                    ON Progs.[program_id] = Task.[program_id]
                WHERE Progs.[deleted] = 0
                AND Progs.[DeletedIncludeParent] = 0
                AND SchedProg.[Deleted] = 0
                AND SchedDay.[schedule_id] IN {schedules_id}
                AND SchedDay.[day_date] BETWEEN '{start_date}' AND DATEADD(DAY, {work_duration}, '{start_date}')
                AND Progs.[program_type_id] IN {program_type}
                AND Progs.[program_id] > 0
                AND Progs.[program_id] NOT IN
                    (SELECT DISTINCT [ObjectId] FROM [{OPLAN_DB}].[dbo].[ProgramCustomFieldValues]
                    WHERE [ProgramCustomFieldId] = 15 OR [ProgramCustomFieldId] = 7)
                AND Progs.[program_id] NOT IN
                    (SELECT [program_id] FROM [{PLANNER_DB}].[dbo].[task_list])
                AND Task.[worker_id] IS NULL
                ORDER BY SchedProg.[DateTime] ASC
            '''
            cursor.execute(new_tasks_query)
            for material in cursor.fetchall():
                material_list.append({**dict(zip(django_columns, material)), 'is_remake': False})
        except Exception as error:
            print(error)

        # Запрос для задач на переделку (уже сделанных в 2023)
        try:
            remake_tasks_query = f'''
                SELECT DISTINCT {sql_columns}
                FROM [{OPLAN_DB}].[dbo].[program] AS Progs
                JOIN [{OPLAN_DB}].[dbo].[scheduled_program] AS SchedProg
                    ON Progs.[program_id] = SchedProg.[program_id]
                JOIN [{OPLAN_DB}].[dbo].[schedule_day] AS SchedDay
                    ON SchedProg.[schedule_day_id] = SchedDay.[schedule_day_id]
                LEFT JOIN [{PLANNER_DB}].[dbo].[task_list] AS Task
                    ON Progs.[program_id] = Task.[program_id]
                WHERE Progs.[deleted] = 0
                AND Progs.[DeletedIncludeParent] = 0
                AND SchedProg.[Deleted] = 0
                AND SchedDay.[schedule_id] IN {schedules_id}
                AND SchedDay.[day_date] BETWEEN '{start_date}' AND DATEADD(DAY, {work_duration}, '{start_date}')
                AND Progs.[program_type_id] IN {program_type}
                AND Progs.[program_id] > 0
                AND Progs.[program_id] IN
                    (SELECT DISTINCT [ObjectId] FROM [{OPLAN_DB}].[dbo].[ProgramCustomFieldValues]
                    WHERE [DateValue] BETWEEN '2023-01-01' AND '2024-01-01')
                AND Progs.[program_id] NOT IN
                    (SELECT [program_id] FROM [{PLANNER_DB}].[dbo].[task_list])
                AND Task.[worker_id] IS NULL
                ORDER BY SchedProg.[DateTime] ASC
            '''

            cursor.execute(remake_tasks_query)
            for material in cursor.fetchall():
                material_list.append({**dict(zip(django_columns, material)), 'is_remake': True})

        except Exception as error:
            print(error)

    return material_list


def create_distribution_plan(material_list, start_distribution_date, remake_percent):
    distribution_plan = []
    current_date = start_distribution_date

    # Словарь для отслеживания нагрузки сотрудников по дням
    daily_worker_load = {}

    def get_daily_load(work_date):
        if work_date not in daily_worker_load:
            daily_worker_load[work_date] = get_real_daily_load(work_date)
        return daily_worker_load[work_date]

    def find_worker_for_date(work_date, duration):
        daily_load = get_daily_load(work_date)
        available_workers = {wid: load for wid, load in daily_load.items()
                             if load + duration <= 720000.0}
        if not available_workers:
            return None, work_date
        worker_id = min(available_workers.items(), key=lambda x: x[1])[0]
        return worker_id, work_date

    def update_worker_load(work_date, worker_id, duration):
        if work_date not in daily_worker_load:
            daily_worker_load[work_date] = {}
        daily_worker_load[work_date][worker_id] = daily_worker_load[work_date].get(worker_id, 0) + duration

    # Разделяем задачи
    program_id_list = []
    series_tasks = {}
    film_tasks = []

    for material in material_list:
        program_id = material.get('Progs_program_id')
        if program_id in program_id_list:
            continue
        program_id_list.append(program_id)

        program_type = material.get('Progs_program_type_id')
        parent_id = material.get('Progs_parent_id')

        if program_type in (4, 8, 12) and parent_id:
            if parent_id not in series_tasks:
                series_tasks[parent_id] = []
            series_tasks[parent_id].append(material)
        else:
            film_tasks.append(material)

    # Создаем группы сериалов с сортировкой по номеру серии
    series_groups = []
    for parent_id, tasks in series_tasks.items():
        # Сортируем серии по возрастанию номера
        sorted_tasks = sorted(tasks, key=lambda x: x.get('Progs_episode_num', 0))

        # Создаем группы по 1-3 серии в правильном порядке
        for i in range(0, len(sorted_tasks), 3):
            series_group = sorted_tasks[i:i + 3]
            series_groups.append({
                'tasks': series_group,
                'total_duration': sum(task.get('Progs_duration', 0.0) for task in series_group)
            })

    # Перемешиваем группы сериалов (но серии внутри групп остаются отсортированными)
    random.shuffle(series_groups)

    # Перемешиваем фильмы
    random.shuffle(film_tasks)

    # Разделяем фильмы на remake и обычные
    remake_tasks = [task for task in film_tasks if task.get('is_remake')]
    new_tasks = [task for task in film_tasks if not task.get('is_remake')]

    # Счетчики для соблюдения процента remake
    current_remake_count = 0
    current_total_count = 0

    # Распределяем сериалы
    for series_group in series_groups:
        duration = series_group['total_duration']

        # Ищем дату и сотрудника для всей группы
        temp_date = current_date
        while True:
            worker_id, work_date = find_worker_for_date(temp_date, duration)
            if worker_id:
                break
            temp_date += timedelta(days=1)

        day_plan = find_or_create_day_plan(distribution_plan, work_date)

        # Добавляем все серии группы (они уже отсортированы по номеру)
        for task in series_group['tasks']:
            task['worker_id'] = worker_id
            task['work_date'] = work_date
            day_plan['tasks'].append(task)
            day_plan['total_duration'] += task.get('Progs_duration', 0.0)
            update_worker_load(work_date, worker_id, task.get('Progs_duration', 0.0))

            # Обновляем счетчики для сериалов-remake
            if task.get('is_remake'):
                current_remake_count += 1
            current_total_count += 1

    # Распределяем фильмы с учетом процента remake
    for i, task in enumerate(film_tasks):
        duration = task.get('Progs_duration', 0.0)
        is_remake = task.get('is_remake', False)

        # Проверяем процент remake в текущем распределении
        current_percent = (current_remake_count / (current_total_count + 1)) * 100 if current_total_count > 0 else 0

        # # Если это remake и превышен лимит, пропускаем (но это не должно случиться из-за перемешивания)
        # if is_remake and current_percent >= remake_percent:
        #     # Можно добавить логику для пропуска или отложить на следующий день
        #     continue

        # Ищем сотрудника
        temp_date = current_date
        while True:
            worker_id, work_date = find_worker_for_date(temp_date, duration)
            if worker_id:
                break
            temp_date += timedelta(days=1)

        day_plan = find_or_create_day_plan(distribution_plan, work_date)

        # Добавляем задачу
        task['worker_id'] = worker_id
        task['work_date'] = work_date
        day_plan['tasks'].append(task)
        day_plan['total_duration'] += duration
        update_worker_load(work_date, worker_id, duration)

        # Обновляем счетчики
        if is_remake:
            current_remake_count += 1
        current_total_count += 1

    return distribution_plan

def find_or_create_day_plan(distribution_plan, work_date):
    """Находит или создает план на день"""
    for day in distribution_plan:
        if day['work_date'] == work_date:
            return day

    new_day = {
        'work_date': work_date,
        'tasks': [],
        'total_duration': 0
    }
    distribution_plan.append(new_day)
    return new_day

def get_real_daily_load(work_date):
    """Получает реальную нагрузку сотрудников из БД на дату"""
    with connections[PLANNER_DB].cursor() as cursor:
        query = f'''
        DECLARE @target_date DATE
        SET @target_date = %s
        SELECT
            Eng.[worker_id] AS worker_id,
            COALESCE(SUM(Task.[duration]), 0) AS total_duration
        FROM
            [{PLANNER_DB}].[dbo].[engineers_list] AS Eng
        LEFT JOIN [{PLANNER_DB}].[dbo].[task_list] AS Task
            ON Eng.[worker_id] = Task.[worker_id]
            AND Task.[work_date] = @target_date
        LEFT JOIN [{PLANNER_DB}].[dbo].[days_off] AS Days
            ON Days.[day_off] = @target_date
        LEFT JOIN [{PLANNER_DB}].[dbo].[vacation_schedule] AS Vac
            ON Eng.[worker_id] = Vac.[worker_id]
            AND @target_date BETWEEN Vac.[start_date] AND Vac.[end_date]
        WHERE Days.[day_off] IS NULL AND Vac.[vacation_id] IS NULL
        GROUP BY Eng.[worker_id]
        '''
        cursor.execute(query, (work_date,))
        return {row[0]: row[1] for row in cursor.fetchall()}

def check_date(obj):
    if isinstance(obj, str):
        try:
            return datetime.strptime(obj, '%Y-%m-%d').date()
        except Exception as error:
            print(error)
            return date.today()
    elif isinstance(obj, (datetime, date)):
        return obj
    return date.today()