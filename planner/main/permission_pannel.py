from django.db import connections


def ask_db_permissions(worker_id):
    with (connections['planner'].cursor() as cursor):
        perm_list = ('home', 'day', 'on_air_report', 'week', 'list', 'kpi_info', 'work_calendar',
                     'common_pool', 'full_info_card', 'otk', 'advanced_search', 'messenger')
        columns = ', '.join([f'[{perm}]' for perm in perm_list])
        query = f'''
        SELECT {columns} FROM [planner].[dbo].[worker_list] AS Worker
        JOIN [planner].[dbo].[permission_list] AS Perm
            ON Worker.[permission_group] = Perm.[permission_group]
        WHERE Worker.[worker_id] = {worker_id}
        '''
        cursor.execute(query)
        perm_val = cursor.fetchone()
        if perm_val:
            return dict(zip(perm_list, perm_val))
