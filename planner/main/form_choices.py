from django.db import connections


def program_custom_fields():
    with connections['oplan3'].cursor() as cursor:
        query = f'''
        SELECT [CustomFieldID], [ItemsString]
        FROM [oplan3].[dbo].[ProgramCustomFields]
        WHERE [CustomFieldID] IN (15, 18, 19)
        '''
        print(query)
        cursor.execute(query)
        fields_list = cursor.fetchall()
        fields_dict = {}
        if fields_list:
            for field_id, items_string in fields_list:
                fields_dict[field_id] = items_string
        return fields_dict



class Choices:
    def __init__(self):
        self.custom_fields = program_custom_fields()

    def tags(self, label='-'):
        tags = self.custom_fields.get(18)
        tags_list = [('', label)]
        if tags:
            for tag in enumerate(tags.split('\r\n')):
                if tag[1]:
                    tags_list.append(tag)
        return tags_list

    def inoagents(self, label='-'):
        inoagents = self.custom_fields.get(19)
        inoagents_list = [('', label)]
        if inoagents:
            for inoagent in enumerate(inoagents.split('\r\n')):
                if inoagent[1]:
                    inoagents_list.append(inoagent)
        return inoagents_list

    def engineers(self, label='-'):
        engineers = self.custom_fields.get(15)
        engineers_list = [('', label)]
        if engineers:
            for engineer in enumerate(engineers.split('\r\n')):
                # print(engineer)
                if engineer[1]:
                    engineers_list.append(engineer)
        return engineers_list

    def rate(self, label='-'):
        return (('', label), (0, '0+'), (1, '6+'), (2, '12+'), (3, '16+'), (4, '18+'))

    def schedules(self, label='-'):
        return [
            ('', label),
            (3, 'Крепкое'),
            (5, 'Планета дети'),
            (6, 'Мировой сериал'),
            (7, 'Мужской сериал'),
            (8, 'Наше детство'),
            (9, 'Романтичный сериал'),
            (10, 'Наше родное кино'),
            (11, 'Семейное кино'),
            (12, 'Советское родное кино'),
            (20, 'Кино +')
        ]

    def task_status(self, label='-'):
        return [
            ('', label),
            ('no_material', 'Материал отсутствует'),
            ('not_ready', 'Не готов'),
            ('fix', 'Исправление исходника'),
            ('ready', 'Отсмотрен'),
            ('otk', 'Прошёл ОТК'),
            ('otk_fail', 'На доработке'),
            ('final', 'Готов к эфиру'),
            ('ready_fail', 'На пересмотр')
        ]

    def material_type(self, label='-'):
        return [
            ('', label),
            ('film', 'Фильм'),
            ('season', 'Сериал')
        ]