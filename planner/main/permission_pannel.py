from django.db import connections

def ask_permissions(worker_id):
    admin = [0, 1]
    preparation_engineer = []
    broadcast_engineer = []
    otk = []
    editor = [2, 3, 4, 5]

    if worker_id in admin:
        return ['day', 'week', 'month', 'list']
    elif worker_id in preparation_engineer:
        return ['day', 'week', 'list', 'full_info_card', 'common_pool']
    elif worker_id in broadcast_engineer:
        return ['month', 'full_info_card']
    elif worker_id in otk:
        return ['month', 'full_info_card']
    elif worker_id in editor:
        return ['month', 'full_info_card']
    else:
        return []

def ask_db_permissions(perm, worker_id):
    with connections['planner'].cursor() as cursor:
        query = f'''
        SELECT {perm} FROM [planner].[dbo].[worker_list] AS Worker
        JOIN [planner].[dbo].[permission_list] AS Perm
            ON Worker.[permission_group] = Perm.[permission_group]
        WHERE Worker.[worker_id] = {worker_id}
        '''
        cursor.execute(query)
        answer = cursor.fetchone()
        if answer:
            return answer[0]
