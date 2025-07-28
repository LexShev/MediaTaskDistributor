from django.db import connections
from planner.settings import OPLAN_DB, PLANNER_DB

def ask_db_permissions(worker_id):
    with connections[PLANNER_DB].cursor() as cursor:
        perm_list = ('home', 'day', 'on_air_report', 'week', 'list', 'kpi_info', 'work_calendar', 'common_pool',
                     'full_info_card', 'otk', 'advanced_search', 'task_manager', 'messenger', 'desktop')
        columns = ', '.join([f'[{perm}]' for perm in perm_list])
        query = f'''
        SELECT {columns} FROM [{PLANNER_DB}].[dbo].[worker_list] AS Worker
        JOIN [{PLANNER_DB}].[dbo].[permission_list] AS Perm
            ON Worker.[permission_group] = Perm.[permission_group]
        WHERE Worker.[worker_id] = {worker_id}
        '''
        cursor.execute(query)
        perm_val = cursor.fetchone()
        if perm_val:
            return dict(zip(perm_list, perm_val))
