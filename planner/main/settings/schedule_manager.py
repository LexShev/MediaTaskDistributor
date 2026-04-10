from main.settings.main_settings import main_settings


class ScheduleManager:
    """
    Управление данными каналов/сеток вещания.

    Предоставляет быстрый доступ к информации о каналах
    по ID канала и по ID редактора.
    """
    schedule_dict = {
        3: (17, 'Крепкое', 'krepkoe'),
        5: (40, 'Планета дети', 'planeta_deti'),
        6: (12, 'Мировой сериал', 'mirovoi_serial'),
        7: (17, 'Мужской сериал', 'muzhskoi_serial'),
        8: (12, 'Наше детство', 'nashe_detstvo'),
        9: (40, 'Романтичный сериал', 'romantichnyi_serial'),
        10: (15, 'Наше родное кино', 'nashe_rodnoe_kino'),
        11: (12, 'Семейное кино', 'semeinoe_kino'),
        12: (17, 'Советское родное кино', 'sovetskoe_rodnoe_kino'),
        20: (16, 'Кино +', 'kino+'),
        36: (16, 'Кино Индии', 'kino_indii')

    }

    def __init__(self):
        self._by_editor = {}
        self._build_indexes()
        self.main_settings = main_settings

    def _build_indexes(self):
        """Строит индексы для быстрого поиска"""
        for schedule_id, schedule_info in self.schedule_dict.items():

            # Индекс по редактору (один редактор может вести несколько каналов)
            editor_id = schedule_info[0]
            if editor_id not in self._by_editor:
                self._by_editor[editor_id] = []
            self._by_editor[editor_id].append(schedule_id)

    def get_all_schedules(self):
        return list(self.schedule_dict.keys())

    def get_all_editors(self):
        return list(self._by_editor.keys())

    def get_editor_id_by_schedule(self, schedule_id: int):
        return self.schedule_dict.get(schedule_id, (None, None, None))[0]

    def get_schedule_name_by_id(self, schedule_id: int):
        return self.schedule_dict.get(schedule_id, (None, None, None))[1]

    def get_image_name_by_id(self, schedule_id: int):
        return self.schedule_dict.get(schedule_id, (None, None, None))[2]

    def get_schedules_by_editor(self, editor_id: int):
        return self._by_editor.get(editor_id, [])

    def get_editor_name_by_id(self, editor_id: int):
        return self.main_settings.get_oplan_workers_dict().get(editor_id, '')

    def get_schedule_info(self, schedule_id: int):
        """Получить полную информацию о канале"""
        info = self.schedule_dict.get(schedule_id)
        return {
            'schedule_id': schedule_id,
            'editor_id': info[0],
            'editor_name': self.get_editor_name_by_id(info[0]),
            'schedule_name': info[1],
            'image_name': info[2]
        } if info else {}

    def get_editors_with_schedules(self):
        """
        Возвращает словарь {editor_id: [schedule_id1, schedule_id2, ...]}
        """
        return self._by_editor.copy()

schedule_manager = ScheduleManager()