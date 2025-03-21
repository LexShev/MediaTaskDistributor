from django.db import connections

def insert_action(**kwargs):
    # columns = ('action_description', 'action_comment', 'worker_id', 'worker', 'change_date', 'old_meta', 'new_meta',
    #            'old_work_date', 'new_work_date', 'old_cenz_rate', 'new_cenz_rate', 'old_cenz_worker', 'new_cenz_worker',
    #            'old_tags', 'new_tags', 'old_inoagent', 'new_inoagent', 'old_lgbt', 'new_lgbt', 'old_sig', 'new_sig',
    #            'old_obnazh', 'new_obnazh', 'old_narc', 'new_narc', 'old_mat', 'new_mat', 'old_other', 'new_other',
    #            'old_editor', 'new_editor')
    # values = ('test_description', 'test_comment', 1, 'Ольга Кузовкина', '2025-03-13', 0, 1,
    #            '2025-03-13', '2025-03-13', 'old_cenz_rate', 'new_cenz_rate', 'old_cenz_worker', 'new_cenz_worker',
    #            'old_test_tags', 'test_tags', 'old_inoagent', 'new_inoagent', 'old_lgbt', 'new_lgbt', 'old_sig', 'new_sig',
    #            'old_obnazh', 'new_obnazh', 'old_narc', 'new_narc', 'old_mat', 'new_mat', 'old_other', 'new_other',
    #            'Ольга Кузовкина', 'Дмитрий Гатенян')
    print('kwargs', kwargs)
    sql_columns = ', '.join(kwargs.keys())
    with connections['planner'].cursor() as cursor:
        query = f'INSERT INTO [planner].[dbo].[history_list] ({sql_columns}) VALUES {tuple(kwargs.values())};'
        print(query)
        cursor.execute(query)

def select_actions(program_id):
    columns = ['action_id', 'program_id', 'action_description', 'action_comment', 'worker_id', 'worker',
               'date_of_change', 'old_meta', 'new_meta', 'old_work_date', 'new_work_date', 'old_cenz_rate',
               'new_cenz_rate', 'old_cenz_worker', 'new_cenz_worker', 'old_tags', 'new_tags', 'old_inoagent',
               'new_inoagent', 'old_lgbt', 'new_lgbt', 'old_sig', 'new_sig', 'old_obnazh', 'new_obnazh',
               'old_narc', 'new_narc', 'old_mat', 'new_mat', 'old_other', 'new_other', 'old_editor', 'new_editor']

    sql_columns = ', '.join(columns)
    with connections['planner'].cursor() as cursor:
        query = f'SELECT {sql_columns} FROM[planner].[dbo].[history_list] WHERE [program_id] = {program_id}'
        cursor.execute(query)

        return [dict(zip(columns, actions)) for actions in cursor.fetchall()]


