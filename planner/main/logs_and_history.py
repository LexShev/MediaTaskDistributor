from django.db import connections
from datetime import datetime, date

def check_data_type(value):
    if isinstance(value, datetime) or isinstance(value, date):
        return value.strftime('%Y-%m-%d')
    if value == None:
        return ''
    else:
        return str(value)

def insert_history(service_info_dict, old_values_dict, new_values_dict):
    program_id = service_info_dict.get('program_id')
    worker_id = service_info_dict.get('worker_id')

    columns = ('program_id', 'CustomFieldID', 'action_description', 'action_comment',
               'worker_id', 'time_of_change', 'old_value', 'new_value')
    sql_columns = ', '.join(columns)

    for old_field_id, new_field_id in zip(old_values_dict, new_values_dict):
        old_value, new_value = old_values_dict.get(old_field_id), new_values_dict.get(new_field_id)
        old_value, new_value = check_data_type(old_value), check_data_type(new_value)
        if str(old_value) != str(new_value):
            with connections['planner'].cursor() as cursor:
                query = f'''
                INSERT INTO [planner].[dbo].[history_list] ({sql_columns})
                VALUES ({program_id}, {old_field_id}, '', '', {worker_id}, GETDATE(), '{old_value}', '{new_value}');
                '''
                print(query)
                cursor.execute(query)

def select_actions(program_id):
    columns = ('program_id', 'CustomFieldID', 'action_description', 'action_comment',
               'worker_id', 'time_of_change', 'old_value', 'new_value')
    sql_columns = ', '.join(columns)
    with connections['planner'].cursor() as cursor:
        query = f'SELECT {sql_columns} FROM [planner].[dbo].[history_list] WHERE [program_id] = {program_id}'
        cursor.execute(query)
        return [dict(zip(columns, actions)) for actions in cursor.fetchall()]


