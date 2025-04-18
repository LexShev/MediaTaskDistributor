from django.db import connections

def program_custom_fields():
    with connections['oplan3'].cursor() as cursor:
        query = f'''
        SELECT [CustomFieldID], [ItemsString]
        FROM [oplan3].[dbo].[ProgramCustomFields]
        WHERE [CustomFieldID] IN (15, 18, 19)
        '''
        cursor.execute(query)
        fields_list = cursor.fetchall()
        fields_dict = {}
        if fields_list:
            for field_id, items_string in fields_list:
                fields_dict[field_id] = items_string
        return fields_dict


class Engineers:
    engineers_list = program_custom_fields().get(15)
    choices = [('', '-')]
    if engineers_list:
        for engineer in enumerate(engineers_list.split('\r\n')):
            if engineer[1]:
                choices.append(engineer)

class Tags:
    tags_list = program_custom_fields().get(18)
    choices = [('', '-')]
    if tags_list:
        for tag in enumerate(tags_list.split('\r\n')):
            if tag[1]:
                choices.append(tag)

class Inoagents:
    inoagents_list = program_custom_fields().get(19)
    choices = [('', '-')]
    if inoagents_list:
        for inoagent in enumerate(inoagents_list.split('\r\n')):
            if inoagent[1]:
                choices.append(inoagent)

class Rate:
    choices = (('', '-'), (0, '0+'), (1, '6+'), (2, '12+'), (3, '16+'), (4, '18+'))

class Schedules:
    choices = [
        ('', '-'),
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

class TaskStatus:
    def __init__(self, label='-'):
        self.label = label

    def choices(self):
        choices_list = [
            ('', self.label),
            ('no_material', 'Материал отсутствует'),
            ('not_ready', 'Не готов'),
            ('fix', 'На доработке'),
            ('ready', 'Отсмотрен'),
            ('otk', 'Прошёл ОТК'),
            ('otk_fail', 'НЕ прошёл ОТК'),
            ('final', 'Готов к эфиру'),
            ('ready_fail', 'На пересмотр')
        ]
        return choices_list


class MaterialType:
    choices = [
        ('', '-'),
        ('film', 'Фильм'),
        ('season', 'Сериал')
    ]
    
