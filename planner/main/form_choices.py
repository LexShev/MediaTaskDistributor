from datetime import datetime

from django.db import connections
from planner.settings import OPLAN_DB, PLANNER_DB


def program_custom_fields():
    with connections[OPLAN_DB].cursor() as cursor:
        query = f'''
        SELECT [CustomFieldID], [ItemsString]
        FROM [{OPLAN_DB}].[dbo].[ProgramCustomFields]
        WHERE [CustomFieldID] IN (15, 18, 19)
        '''
        cursor.execute(query)
        fields_list = cursor.fetchall()
        fields_dict = {}
        if fields_list:
            for field_id, items_string in fields_list:
                fields_dict[field_id] = items_string
        return fields_dict

def db_workers_list():
    with connections[PLANNER_DB].cursor() as cursor:
        query = 'SELECT [worker_id], [full_name] FROM [planner].[dbo].[engineers_list]'
        cursor.execute(query)
        return cursor.fetchall() or ()

class Choices:
    def __init__(self):
        self.custom_fields = program_custom_fields()
        self.workers_list = None

    def tags(self, label='-'):
        tags = self.custom_fields.get(18)
        tags_list = [('', label)]
        if tags:
            for tag in enumerate(tags.split('\r\n')):
                if tag[1]:
                    tags_list.append(tag)
        return tags_list

    def inoagents(self, label='-', exclude_init=False):
        inoagents = self.custom_fields.get(19)
        inoagents_list = [('', label)]
        if exclude_init:
            inoagents_list = []
        if inoagents:
            for inoagent in inoagents.split('\r\n'):
                if inoagent:
                    point = (inoagent, inoagent)
                    inoagents_list.append(point)
        return sorted(inoagents_list)

    def engineers(self, label='-', exclude_init=False):
        engineers = self.custom_fields.get(15)
        engineers_list = [('', label)]
        if exclude_init:
            engineers_list = []
        if engineers:
            for engineer in enumerate(engineers.split('\r\n')):
                if engineer[1]:
                    engineers_list.append(engineer)
        return engineers_list

    def workers(self, label='-', exclude_init=False):
        self.workers_list = [('', label)]
        if exclude_init:
            self.workers_list = []
        with connections[PLANNER_DB].cursor() as cursor:
            cursor.execute('SELECT [worker_id], [full_name] FROM [planner].[dbo].[engineers_list]')
            self.workers_list.extend(cursor.fetchall() or ())
        return self.workers_list or []

    def editors(self, label='-', exclude_init=False):
        self.editors_list = [('', label)]
        if exclude_init:
            self.editors_list = []
        with connections[PLANNER_DB].cursor() as cursor:
            cursor.execute('SELECT [planner_editor_id], [full_name] FROM [planner].[dbo].[editors_list]')
            self.editors_list.extend(cursor.fetchall() or ())
        return self.editors_list or []

    def sorting(self):
        return (
            ('sched_date', 'дате эфира'),
            ('work_date', 'дате выполнения'),
            ('name', 'названию'),
            ('duration', 'хронометражу')
        )

    def planner_workers(self, label='-', exclude_init=False):
        with connections[PLANNER_DB].cursor() as cursor:
            query = f'SELECT [username], [first_name], [last_name] FROM [{PLANNER_DB}].[dbo].[auth_user]'
            cursor.execute(query)
            planner_workers = cursor.fetchall()

            planner_workers_list = [('', label)]
            if exclude_init:
                planner_workers_list = []
            if planner_workers:
                for username, first_name, last_name in planner_workers:
                    planner_workers_list.append((username, f'{first_name} {last_name}'))
            return planner_workers_list

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
        return [(year, str(year)) for year in range(current_year-3, current_year+4)]


choice = Choices()