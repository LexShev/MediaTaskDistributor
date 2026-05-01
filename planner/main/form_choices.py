from datetime import datetime

from django.db import connections
from planner.settings import OPLAN_DB, PLANNER_DB


class Choices:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # Загружаем ОДИН РАЗ из БД
        self._custom_fields = self._load_custom_fields()
        self._workers_raw = self._load_workers()
        self._editors_raw = self._load_editors()
        self._planner_workers_raw = self._load_planner_workers()

    # Приватные методы загрузки (вызываются только в __init__)
    def _load_custom_fields(self):
        with connections[OPLAN_DB].cursor() as cursor:
            cursor.execute(f'''
                SELECT [CustomFieldID], [ItemsString]
                FROM [{OPLAN_DB}].[dbo].[ProgramCustomFields]
                WHERE [CustomFieldID] IN (15, 18, 19)
            ''')
            fields = cursor.fetchall()
        return {field_id: items_string for field_id, items_string in fields} if fields else {}

    def _load_workers(self):
        with connections[PLANNER_DB].cursor() as cursor:
            cursor.execute('SELECT [worker_id], [full_name] FROM [planner].[dbo].[engineers_list]')
            return cursor.fetchall() or ()

    def _load_editors(self):
        with connections[PLANNER_DB].cursor() as cursor:
            cursor.execute('SELECT [planner_editor_id], [full_name] FROM [planner].[dbo].[editors_list]')
            return cursor.fetchall() or ()

    def _load_planner_workers(self):
        with connections[PLANNER_DB].cursor() as cursor:
            cursor.execute(f'SELECT [username], [first_name], [last_name] FROM [{PLANNER_DB}].[dbo].[auth_user]')
            return cursor.fetchall() or ()

    # Методы отдачи — только форматируют данные из словарей
    def tags(self, label='-'):
        tags = self._custom_fields.get(18)
        tags_list = [('', label)]
        if tags:
            for tag in enumerate(tags.split('\r\n')):
                if tag[1]:
                    tags_list.append(tag)
        return tags_list

    def inoagents(self, label='-', exclude_init=False):
        inoagents = self._custom_fields.get(19)
        inoagents_list = [] if exclude_init else [('', label)]
        if inoagents:
            for inoagent in inoagents.split('\r\n'):
                if inoagent:
                    inoagents_list.append((inoagent, inoagent))
        return sorted(inoagents_list)

    def engineers(self, label='-', exclude_init=False):
        engineers = self._custom_fields.get(15)
        engineers_list = [] if exclude_init else [('', label)]
        if engineers:
            for engineer in enumerate(engineers.split('\r\n')):
                if engineer[1]:
                    engineers_list.append(engineer)
        return engineers_list

    def workers(self, label='-', exclude_init=False):
        workers_list = [] if exclude_init else [('', label)]
        workers_list.extend(self._workers_raw)
        return workers_list

    def editors(self, label='-', exclude_init=False):
        editors_list = [] if exclude_init else [('', label)]
        editors_list.extend(self._editors_raw)
        return editors_list

    def planner_workers(self, label='-', exclude_init=False):
        planner_workers_list = [] if exclude_init else [('', label)]
        for username, first_name, last_name in self._planner_workers_raw:
            planner_workers_list.append((username, f'{first_name} {last_name}'))
        return planner_workers_list

    # Статические методы (не зависят от БД)
    def sorting(self):
        return (
            ('sched_date', 'дате эфира'),
            ('work_date', 'дате выполнения'),
            ('name', 'названию'),
            ('duration', 'хронометражу')
        )

    def rate(self, label='-'):
        return (('', label), (0, '0+'), (1, '6+'), (2, '12+'), (3, '16+'), (4, '18+'))

    def schedules(self, label='-'):
        return [
            ('', label),
            (1, 'Общая задача'),
            (3, 'Крепкое'),
            (5, 'Планета дети'),
            (6, 'Мировой сериал'),
            (7, 'Мужской сериал'),
            (8, 'Наше детство'),
            (9, 'Романтичный сериал'),
            (10, 'Наше родное кино'),
            (11, 'Семейное кино'),
            (12, 'Советское родное кино'),
            (20, 'Кино +'),
            (36, 'Кино Индии'),
            (99, 'Мои задачи')
        ]

    def channels(self):
        return [
            ('', 'Все'),
            (3, 'Крепкое'),
            (5, 'Планета дети'),
            (6, 'Мировой сериал'),
            (7, 'Мужской сериал'),
            (8, 'Наше детство'),
            (9, 'Романтичный сериал'),
            (10, 'Наше родное кино'),
            (11, 'Семейное кино'),
            (12, 'Советское родное кино'),
            (20, 'Кино +'),
            (36, 'Кино Индии'),
        ]

    def task_status(self, label='-', extra=None):
        status_list = [
            ('', label),
            ('no_material', 'Материал отсутствует'),
            ('not_ready', 'Не готов'),
            ('fix', 'Исправление исходника'),
            ('fix_ready', 'Исходник исправлен'),
            ('ready', 'Отсмотрен'),
            ('otk', 'Прошёл ОТК'),
            ('otk_fail', 'Не прошёл ОТК'),
            ('final', 'Готов к эфиру'),
            ('final_fail', 'Не прошёл ЭК')
        ]
        if extra:
            status_list.extend(extra)
        return status_list

    def read_status(self, label='-', extra=None):
        status_list = [
            ('', label),
            (1, 'Прочитано'),
            (0, 'Не прочитано'),
        ]
        if extra:
            status_list.extend(extra)
        return status_list

    def notification_type(self, label='-', extra=None):
        notification_type_list = [
            ('', label),
            ('info', 'Информационное'),
            ('status', 'Изменение статуса'),
            ('update', 'Обновление сеток'),
            ('error', 'Ошибка'),
        ]
        if extra:
            notification_type_list.extend(extra)
        return notification_type_list

    def mark(self, label='-'):
        return [
            ('', label),
            ('remake', 'Пересмотр'),
            ('archived', 'В архиве'),
        ]

    def extra_set(self, label='-'):
        return [
            ('', label),
            ('deleted', 'Удалено'),
            ('archived', 'В архиве'),
            ('no_cenz', 'Была цензура'),
        ]

    def material_type(self, label='-'):
        return [
            ('', label),
            ('film', 'Фильм'),
            ('season', 'Сериал')
        ]

    def sql_set(self):
        return [
            (100, 'Первые 100'),
            (500, 'Первые 500'),
            (1000, 'Первые 1 000'),
            (10000, 'Первые 10 000'),
            (100000, 'Первые 100 000'),
        ]

    def months(self):
        return [
            (1, "Январь"),
            (2, "Февраль"),
            (3, "Март"),
            (4, "Апрель"),
            (5, "Май"),
            (6, "Июнь"),
            (7, "Июль"),
            (8, "Август"),
            (9, "Сентябрь"),
            (10, "Октябрь"),
            (11, "Ноябрь"),
            (12, "Декабрь")
        ]

    def years(self):
        current_year = datetime.now().year
        return [(year, str(year)) for year in range(current_year - 3, current_year + 4)]

def get_choice():
    return Choices()