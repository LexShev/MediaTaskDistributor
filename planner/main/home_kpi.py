from datetime import datetime, timedelta

from django.db import connections

from planner.settings import PLANNER_DB


def common_kpi():
    today = datetime.now()
    current_weekday = today.weekday()
    start_date = today - timedelta(days=current_weekday)

    with connections[PLANNER_DB].cursor() as cursor:
        query = f'''
        DECLARE @start_date DATE
        SET @start_date = %s
        SELECT [work_date], CAST(COALESCE(SUM([duration]), 0) AS FLOAT) / (720000.0 * COUNT(DISTINCT [engineer_id])) AS KPI
        FROM [{PLANNER_DB}].[dbo].[task_list]
        WHERE task_status NOT IN ('not_ready', 'no_material')
        AND CONVERT(DATE, [work_date]) BETWEEN CONVERT(DATE, @start_date) AND DATEADD(DAY, 6, CONVERT(DATE, @start_date))
        GROUP BY [work_date]
        ORDER BY [work_date]
        '''
        cursor.execute(query, (start_date,))
        result = cursor.fetchall()
        days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
        if result:
            labels = []
            kpis = []
            for label, kpi in result:
                labels.append(days[label.weekday()])
                kpis.append(kpi)
            return {'labels': labels, 'kpis': kpis}

def daily_kpi():
    with connections[PLANNER_DB].cursor() as cursor:
        query = f'''
        SELECT 
        COUNT(CASE WHEN task_status NOT IN ('ready', 'final', 'otk') AND [work_date] = CONVERT(DATE, GETDATE()) THEN 1 END) AS not_final,
        COUNT(CASE WHEN task_status IN ('ready', 'final', 'otk') AND [work_date] = CONVERT(DATE, GETDATE()) THEN 1 END) AS ready,
        COUNT(CASE WHEN task_status = 'no_material' AND [work_date] = CONVERT(DATE, GETDATE()) THEN 1 END) AS no_material,
        COUNT(CASE WHEN task_status IN ('otk_fail', 'fix', 'ready_fail') AND [work_date] = CONVERT(DATE, GETDATE()) THEN 1 END) AS fix
        FROM [{PLANNER_DB}].[dbo].[task_list]
        '''
        cursor.execute(query)
        labels = ['Не выполнено', 'Выполнено', 'Нет материала', 'На доработке']
        values = cursor.fetchone()
        if values:
            return {'labels': labels, 'values': values}
