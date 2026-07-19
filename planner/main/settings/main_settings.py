from django.db import connections
from planner.settings import OPLAN_DB, PLANNER_DB, SERVICE_TYPE

class MainSettings:
    EXTERNAL_ONLY_TABS = {'cinema_atlas'}

    status_dict = {
        'no_material': 'Материал отсутствует',
        'not_ready': 'Не готов',
        'fix': 'Исправление исходника',
        'fix_ready': 'Исходник исправлен',
        'ready': 'Отсмотрен',
        'otk': 'Прошёл ОТК',
        'otk_fail': 'Не прошёл ОТК',
        'final': 'Готов к эфиру',
        'final_fail': 'Не прошёл ЭК',
        'oplan_ready': 'Отсмотрен в Oplan3',
        'no_task_list': 'Не распределён',
        'common_pool': 'Материал из общего пула',
        'card_error': 'Карточка материала заполнена неверно',
    }

    editors_status_dict = {
        'not_ready': 'Не готов',
        'approval': 'Утверждение',
        'ready': 'Готов',
    }

    color_dict = {
        'no_material': 'danger',
        'not_ready': 'primary',
        'fix': 'warning',
        'fix_ready': 'warning',
        'ready': 'success',
        'otk': 'info',
        'otk_fail': 'danger',
        'final': 'success',
        'final_fail': 'danger',
        'oplan_ready': 'success',
        'no_task_list': 'warning',
        'common_pool': 'info',
        'card_error': 'danger',
    }

    on_air_color_dict = {
        'no_material': 'danger',
        'not_ready': 'danger',
        'fix': 'warning',
        'fix_ready': 'warning',
        'ready': 'warning',
        'otk': 'warning',
        'otk_fail': 'danger',
        'final': 'success',
        'final_fail': 'danger',
        'oplan_ready': 'success',
        'no_task_list': 'warning',
        'common_pool': 'info',
        'card_error': 'danger',
    }

    channel_color_dict = {
        3: {'name': 'red', 'hex': '#dc3545', 'rgb': '220, 53, 69'},  # Крепкое
        5: {'name': 'blue', 'hex': '#0d6efd', 'rgb': '13, 110, 253'},  # Планета дети
        6: {'name': 'yellow', 'hex': '#ffc107', 'rgb': '255, 193, 7'},  # Мировой сериал
        7: {'name': 'orange', 'hex': '#fd7e14', 'rgb': '253, 126, 20'},  # Мужской сериал
        8: {'name': 'cyan', 'hex': '#0dcaf0', 'rgb': '13, 202, 240'},  # Наше детство
        9: {'name': 'pink', 'hex': '#d63384', 'rgb': '214, 51, 132'},  # Романтичный сериал
        10: {'name': 'green', 'hex': '#198754', 'rgb': '25, 135, 84'},  # Наше родное кино
        11: {'name': 'purple', 'hex': '#6f42c1', 'rgb': '111, 66, 193'},  # Семейное кино
        12: {'name': 'teal', 'hex': '#20c997', 'rgb': '32, 201, 151'},  # Советское родное кино
        20: {'name': 'indigo', 'hex': '#6610f2', 'rgb': '102, 16, 242'},  # Кино +
        36: {'name': 'orange-700', 'hex': '#984c0c', 'rgb': '152, 76, 12'}  # Кино Индии
    }

    header_panels = {
        1: {'name': 'moderators', 'label': 'Админ панель', 'tabs':
            ['task_manager', 'kpi_info', 'work_calendar']
            },
        3: {'name': 'broadcast_engineers', 'label': 'Эфирный контроль', 'tabs':
            ['air_day_report', 'air_month_report', 'air_search', 'cinema_atlas', 'advanced_search']
            },
        6: {'name': 'editors', 'label': 'Редакторы', 'tabs':
            ['air_day_report', 'air_month_report', 'common_pool', 'playlist_daily', 'editors_notifications',
             'cinema_atlas', 'advanced_search']
            },
        8: {'name': 'chief_editor', 'label': 'Главный редактор', 'tabs':
            ['air_day_report', 'air_month_report', 'common_pool', 'playlist_daily', 'editors_notifications',
             'advanced_search', 'cinema_atlas']
            },
        4: {'name': 'otk_engineers', 'label': 'ОТК', 'tabs':
            ['otk', 'common_pool', 'advanced_search', 'cinema_atlas']
            },
        2: {'name': 'preparation_engineers', 'label': 'Инженеры подготовки', 'tabs':
            ['week', 'list', 'common_pool', 'advanced_search', 'desktop']
            },
        7: {'name': 'preparation_engineers__editors', 'label': 'Арина', 'tabs':
            ['week', 'list', 'common_pool', 'air_day_report', 'air_month_report', 'desktop', 'playlist_daily', 'editors_notifications', 'advanced_search']
            },
    }

    label_dict = {
        'air_day_report': 'Отчёт на день',
        'air_month_report': 'Отчёт на месяц',
        'air_search': 'Поиск задач',
        'playlist_daily': 'Сетки вещания',
        'editors_notifications': 'Уведомления',
        'schedule_perspective': 'Перспективные сетки',
        'advanced_search': 'Расширенный поиск',
        'cinema_atlas': 'Cinema Atlas',
        'common_pool': 'Общий пул',
        'otk': 'Технический контроль',
        'week': 'Неделя',
        'list': 'Список',
        'desktop': 'Рабочий стол',
        'task_manager': 'Управление задачами',
        'kpi_info': 'KPI',
        'work_calendar': 'Календарь',
    }

    url_dict = {
        'air_day_report': 'on-air-report/today',
        'air_month_report': 'on-air-report/month',
        'air_search': 'on-air-report/search',
        'playlist_daily': 'playlist/daily',
        'editors_notifications': 'playlist/editors_notifications',
        'schedule_perspective': 'schedule-perspective',
        'advanced_search': 'advanced_search',
        'cinema_atlas': 'cinema-atlas',
        'common_pool': 'common_pool',
        'otk': 'otk',
        'week': 'week',
        'list': 'list',
        'desktop': 'desktop',
        'task_manager': 'task_manager',
        'kpi_info': 'kpi_info',
        'work_calendar': 'work_calendar',
    }

    def __init__(self):
        self._oplan_workers_dict = None
        self._planner_workers_dict = None
        self._label_panels = None

    def planner_workers_dict(self):
        try:
            with connections[PLANNER_DB].cursor() as cursor:
                query = f'SELECT [id], [first_name], [last_name] FROM [{PLANNER_DB}].[dbo].[auth_user]'
                cursor.execute(query)
                workers = cursor.fetchall()
                if not workers:
                    return {}
                return {worker[0]: f'{worker[1]} {worker[2]}' for worker in workers}

        except Exception as error:
            print(error)
            return {}

    @property
    def get_planner_workers_dict(self):
        if self._planner_workers_dict is None:
            self._planner_workers_dict = self.planner_workers_dict()
        return self._planner_workers_dict

    def oplan_workers_dict(self):
        try:
            with connections[PLANNER_DB].cursor() as cursor:
                query = f'''
                SELECT [OplanUsers].[oplan_id], [first_name], [last_name]
                FROM [{PLANNER_DB}].[dbo].[auth_user] AS PlannerUsers
                JOIN [{PLANNER_DB}].[dbo].[oplan_users_list] AS OplanUsers
                    ON [PlannerUsers].[id] = OplanUsers.[planner_id]
                '''
                cursor.execute(query)
                results = cursor.fetchall()
                if not results:
                    return {}
                return {worker[0]: f'{worker[1]} {worker[2]}' for worker in results}

        except Exception as error:
            print(error)
            return {}

    @property
    def get_oplan_workers_dict(self):
        if self._oplan_workers_dict is None:
            self._oplan_workers_dict = self.oplan_workers_dict()
        return self._oplan_workers_dict

    def refresh_workers_dict(self):
        """Принудительно обновить словарь сотрудников"""
        self._oplan_workers_dict = self.oplan_workers_dict()
        return self._oplan_workers_dict

    def get_oplan_channels_dict(self, status):
        try:
            return self.editors_status_dict.get(status, '')
        except Exception as error:
            print(error)
            return ''

    def _build_label_panels(self):
        label_panels = {}
        for group_id, department in self.header_panels.items():
            label_panels[group_id] = {
                'name': department['name'],
                'label': department['label'],
                'tabs': [
                    {
                        'key': tab,
                        'label': self.label_dict.get(tab, tab),
                        'url': self.url_dict.get(tab, '')
                    } for tab in department['tabs']
                ],
            }
        return label_panels

    @property
    def label_panels(self):
        if self._label_panels is None:
            self._label_panels = self._build_label_panels()
        return self._label_panels

    def get_header_panels(self, group_id):
        try:
            # group_id = 2
            panels = self.label_panels
            if group_id == 5:
                result = [panels.get(department, {}) for department in panels.keys()]
            elif group_id == 1:
                result = [panels.get(department, {}) for department in panels.keys()]
            else:
                result = [panels.get(group_id, {})]

            if SERVICE_TYPE != 'external':
                for dept in result:
                    if 'tabs' in dept:
                        dept['tabs'] = [
                            tab for tab in dept['tabs']
                            if tab['key'] not in self.EXTERNAL_ONLY_TABS
                        ]
            return result
        except Exception as e:
            print(e)
            return []

_main_settings = None

def get_main_settings():
    global _main_settings
    if _main_settings is None:
        _main_settings = MainSettings()
    return _main_settings

