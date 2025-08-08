import calendar
from datetime import date

from django.db import connections

from planner.settings import PLANNER_DB


def calendar_skeleton():
    today = date.today()
    cal_year, cal_month = today.year, today.month
    month_dates = calendar.Calendar().monthdatescalendar(cal_year, cal_month)
    weeks = []
    for week in month_dates:
        week_data = {'number': week[0].isocalendar()[1], 'days': []}
        for day in week:
            week_data['days'].append({'date': day, 'day': day.day, 'is_current_month': day.month == cal_month})
        weeks.append(week_data)
    return weeks

def update_info(current_date):
    with connections[PLANNER_DB].cursor() as cursor:
        cursor.execute(f'''
        DECLARE @current_date DATE
        SET @current_date = %s
        SELECT
            COUNT(CASE WHEN task_status NOT IN ('ready', 'final', 'otk') AND [work_date] = @current_date THEN 1 END) AS not_ready,
            COUNT(CASE WHEN task_status IN ('ready', 'final', 'otk') AND [work_date] = @current_date THEN 1 END) AS ready
        FROM [{PLANNER_DB}].[dbo].[task_list]
        '''
        , (current_date,))
        result = cursor.fetchone()
        not_ready = result[0] if result and result[0] is not None else 0
        ready = result[1] if result and result[1] is not None else 0
        try:
            ready_index = (ready * 100) / (not_ready + ready)
        except Exception as e:
            print(e)
            ready_index = 'day_off'

        if ready_index == 'day_off':
            color = ''
        elif ready_index == 100:
            color = 'btn-outline-success'
        elif 30 < ready_index <= 99:
            color = 'btn-outline-warning'
        else:
            color = 'btn-outline-danger'

        return {
            'not_ready': not_ready,
            'ready': ready,
            'color': color
        }
