from django.db import connections


def insert_action(service_info_dict, old_values_dict, new_values_dict):
    # if val:
    #     if val == True:
    #         val = 1
    #     if val = 0:
    #         val = '0'
    #     elif isinstance(val, datetime.date):
    #         val = val.strftime('%Y-%m-%d')

    program_id = service_info_dict.get('program_id')
    worker_id = service_info_dict.get('worker_id')
    time_of_change = service_info_dict.get('time_of_change')

    columns = ('program_id', 'CustomFieldID', 'action_description', 'action_comment',
               'worker_id', 'time_of_change', 'old_value', 'new_value')
    sql_columns = ', '.join(columns)

    for old_field_id, new_field_id in zip(old_values_dict, new_values_dict):
        old_value, new_value = old_values_dict.get(old_field_id), new_values_dict.get(new_field_id)
        if old_value == 0:
            old_value = '0'
        if new_value == 0:
            new_value = '0'
        if old_value == None:
            old_value = ''
        if new_value == None:
            new_value = ''
        if str(old_value) != str(new_value):
            with connections['planner'].cursor() as cursor:
                query = f'''
                INSERT INTO [planner].[dbo].[history_list] ({sql_columns})
                VALUES ({program_id}, {old_field_id}, 'NULL', 'NULL', {worker_id}, GETDATE(), '{old_value}', '{new_value}');
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


