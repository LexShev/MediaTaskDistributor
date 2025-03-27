from django.db import connections

def insert_action(service_info_dict, old_values_dict, new_values_dict):
    if val:
        if val == True:
            val = 1
        elif isinstance(val, datetime.date):
            val = val.strftime('%Y-%m-%d')
    print('history_kwargs', kwargs)
    sql_columns = ', '.join(kwargs.keys())
    with connections['planner'].cursor() as cursor:
        query = f'INSERT INTO [planner].[dbo].[history_list] ({sql_columns}) VALUES {tuple(kwargs.values())};'
        print(query)
        cursor.execute(query)

def select_actions(program_id):
    columns = ['action_id', 'program_id', 'action_description', 'action_comment', 'worker_id', 'worker',
               'date_of_change', 'old_meta', 'new_meta', 'old_work_date', 'new_work_date', 'old_cenz_rate',
               'new_cenz_rate', 'old_cenz_worker_id', 'new_cenz_worker_id', 'old_tags', 'new_tags', 'old_inoagent',
               'new_inoagent', 'old_lgbt', 'new_lgbt', 'old_sig', 'new_sig', 'old_obnazh', 'new_obnazh',
               'old_narc', 'new_narc', 'old_mat', 'new_mat', 'old_other', 'new_other', 'old_editor', 'new_editor']

    sql_columns = ', '.join(columns)
    with connections['planner'].cursor() as cursor:
        query = f'SELECT {sql_columns} FROM[planner].[dbo].[history_list] WHERE [program_id] = {program_id}'
        cursor.execute(query)

        return [dict(zip(columns, actions)) for actions in cursor.fetchall()]


