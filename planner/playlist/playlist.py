from datetime import date, datetime

from django.db import connections
from django.http import JsonResponse

from planner.settings import OPLAN_DB

def check_schedule(schedule_id):
    try:
        if not schedule_id:
            return 'AND [schedule_id] IN (3, 5, 6, 7, 8, 9, 10, 11, 12, 20)'
        return f'AND [schedule_id] = {schedule_id}'
    except Exception as error:
        print(error)
        return 'AND [schedule_id] IN (3, 5, 6, 7, 8, 9, 10, 11, 12, 20)'

def check_date(schedule_date):
    today = date.today()
    if not schedule_date or schedule_date == '[]':
        return today, today
    try:
        return [datetime.strptime(str_date, '%d.%m.%Y') for str_date in schedule_date.split(' - ')]
    except Exception as error:
        print(error)
        return today, today

def get_schedule_days(field_dict):
    start_date, end_date = check_date(field_dict.get('schedule_date'))
    with connections[OPLAN_DB].cursor() as cursor:
        query = f"""
        SELECT 
            [schedule_day_id],
            [schedule_id],
            [day_date],
            [approved_for_broadcasting],
            [last_edit_user_id],
            [last_edit_time],
            [DayStatus],
            [AdvertImportDay],
            [PromoImportDay],
            [MusicImportDay],
            [AdvertListImportDay],
            [DayType]
        FROM [{OPLAN_DB}].[dbo].[schedule_day]
        WHERE [day_date] BETWEEN CONVERT(DATE, %s) AND CONVERT(DATE, %s)
        {check_schedule(field_dict.get('schedule_id'))}
        ORDER BY [day_date]
        """

        cursor.execute(query, (start_date, end_date))
        columns = [col[0] for col in cursor.description]
        results = []

        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))

        return results

def get_schedule_day_table(schedule_day_id):
    with connections[OPLAN_DB].cursor() as cursor:
        query = f'''
        SELECT [schedule_day_id]
              ,[program_id]
              ,[start_time]
              ,[duration]
              ,[ad_duration]
              ,[name]
              ,[can_be_moved]
              ,[can_be_inserted]
              ,[scheduled_program_id]
              ,[ParentID]
              ,[SlotType]
              ,[MaterialID]
              ,[PlannedStartTime]
              ,[IsBlock]
              ,[Level]
              ,[program_type_id]
              ,[TheAir]
              ,[Active]
              ,[Premiere]
              ,[ChildPosition]
              ,[Deleted]
              ,[DeletedIncludeParent]
              ,[DateTime]
              ,[LastEditUser]
              ,[CreatedAt]
              ,[CreatedBy]
              ,[LastEditTime]
              ,[LastPlacementPosition]
              ,[MediumName]
          FROM [{OPLAN_DB}].[dbo].[scheduled_program]
          WHERE [schedule_day_id] = %s
          AND [Deleted] = 0
          AND [DeletedIncludeParent] = 0
          ORDER BY [DateTime]
        '''

        cursor.execute(query, (schedule_day_id,))
        columns = [col[0] for col in cursor.description]
        results = []

        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        print('results', results)
    return build_hierarchy_from_level(results)


def build_hierarchy_from_level(schedule_data):
    """
    Преобразует плоский список с полями Level и ParentID в иерархическую структуру
    """
    # Сортируем по уровню вложенности (от меньшего к большему)
    schedule_data.sort(key=lambda x: (x['Level'], x.get('ChildPosition', 0)))

    # Создаем словарь для быстрого поиска по ID
    items_by_id = {}
    root_items = []

    # Первый проход: создаем структуры с пустыми children
    for item in schedule_data:
        item_id = item['scheduled_program_id']
        items_by_id[item_id] = {
            **item,
            'children': [],
            'is_collapsed': True,  # для фронтенда
            'type': 'program' if item.get('program_id') else 'folder' if item.get('SlotType') == 1 else 'segment'
        }

    # Второй проход: строим иерархию
    for item in schedule_data:
        item_id = item['scheduled_program_id']
        parent_id = item.get('ParentID')

        if parent_id is None or parent_id not in items_by_id:
            # Это корневой элемент
            root_items.append(items_by_id[item_id])
        else:
            # Это дочерний элемент
            parent_item = items_by_id[parent_id]
            parent_item['children'].append(items_by_id[item_id])

    return root_items

def create_nested_structure(flat_list, parent_field='ParentID', id_field='scheduled_program_id'):
    """
    Универсальная функция для создания вложенной структуры

    Args:
        flat_list: плоский список словарей
        parent_field: поле, указывающее на родителя
        id_field: поле с уникальным ID

    Returns:
        Вложенный список словарей с ключом 'children'
    """
    # Создаем словарь для быстрого поиска
    item_dict = {item[id_field]: item for item in flat_list}

    # Добавляем пустой список детей каждому элементу
    for item in flat_list:
        item['children'] = []

    # Строим дерево
    root_items = []

    for item in flat_list:
        parent_id = item.get(parent_field)

        if parent_id is None:
            # Это корневой элемент
            root_items.append(item)
        else:
            # Находим родителя
            parent = item_dict.get(parent_id)
            if parent:
                parent['children'].append(item)
            else:
                # Родитель не найден - возможно ошибка данных
                # Добавляем как корневой элемент
                root_items.append(item)

    # Опционально: сортируем детей по какому-либо полю
    # def sort_children(items, sort_key='ChildPosition'):
    #     for item in items:
    #         if item['children']:
    #             item['children'].sort(key=lambda x: x.get(sort_key, 0))
    #             sort_children(item['children'], sort_key)
    #
    # sort_children(root_items)

    return root_items