import calendar
from datetime import date

from django.db import connections

from planner.settings import PLANNER_DB, OPLAN_DB


def calendar_skeleton(cal_year, cal_month):
    today = date.today()
    month_dates = calendar.Calendar().monthdatescalendar(cal_year, cal_month)
    weeks = []
    for week in month_dates:
        week_data = {'number': week[0].isocalendar()[1], 'days': []}
        for day in week:
            week_data['days'].append({'date': day, 'day': day.day,
                                      'is_current_month': day.month == cal_month,
                                      'is_today': day == today})
        weeks.append(week_data)
    return weeks

def sched_sort(schedule_id):
    if not schedule_id:
        return ''
    return f'AND SchedDay.[schedule_id] = {schedule_id}'

def update_info(current_date, schedule_id):
    with connections[PLANNER_DB].cursor() as cursor:
        cursor.execute(f'''
        DECLARE @current_date DATE
        SET @current_date = %s
        SELECT
            COUNT(DISTINCT CASE WHEN Task.[task_status] = 'no_material' THEN Task.[program_id] END) AS no_material,
            COUNT(DISTINCT CASE WHEN Task.[task_status] = 'not_ready' THEN Task.[program_id] END) AS not_ready,
            COUNT(DISTINCT CASE WHEN Task.[task_status] = 'fix' THEN Task.[program_id] END) AS fix,
            COUNT(DISTINCT CASE WHEN Task.[task_status] = 'fix_ready' THEN Task.[program_id] END) AS fix_ready,
            COUNT(DISTINCT CASE WHEN Task.[task_status] = 'ready' THEN Task.[program_id] END) AS ready,
            COUNT(DISTINCT CASE WHEN Task.[task_status] = 'otk' THEN Task.[program_id] END) AS otk,
            COUNT(DISTINCT CASE WHEN Task.[task_status] = 'otk_fail' THEN Task.[program_id] END) AS otk_fail,
            COUNT(DISTINCT CASE WHEN Task.[task_status] = 'final' THEN Task.[program_id] END) AS final,
            COUNT(DISTINCT CASE WHEN Task.[task_status] = 'final_fail' THEN Task.[program_id] END) AS final_fail,
            COUNT(DISTINCT CASE WHEN CustField.[ProgramCustomFieldId] = 15 AND Task.[program_id] IS NULL THEN Progs.[program_id] END) AS ready_oplan3,
            COUNT(DISTINCT Progs.[program_id]) AS total_programs
        FROM [{OPLAN_DB}].[dbo].[program] AS Progs
        JOIN [{OPLAN_DB}].[dbo].[scheduled_program] AS SchedProg
            ON Progs.[program_id] = SchedProg.[program_id]
        JOIN [{OPLAN_DB}].[dbo].[schedule_day] AS SchedDay
            ON SchedProg.[schedule_day_id] = SchedDay.[schedule_day_id]
        JOIN [{OPLAN_DB}].[dbo].[schedule] AS Sched
            ON SchedDay.[schedule_id] = Sched.[schedule_id]
        LEFT JOIN [{PLANNER_DB}].[dbo].[task_list] AS Task
            ON Progs.[program_id] = Task.[program_id]
        LEFT JOIN [{OPLAN_DB}].[dbo].[ProgramCustomFieldValues] AS CustField
            ON Progs.[program_id] = CustField.[ObjectId]
        WHERE SchedDay.[day_date] = @current_date
        {sched_sort(schedule_id)}
        AND Progs.[program_id] > 0
        AND Progs.[deleted] = 0
        AND Progs.[DeletedIncludeParent] = 0
        AND Progs.[program_type_id] IN (4, 5, 6, 7, 8, 10, 11, 12, 16, 19, 20)
        AND SchedProg.[Deleted] = 0
        '''
        , (current_date,))
        result = cursor.fetchone()
        if result:
            no_material, not_ready, fix, fix_ready, ready, otk, otk_fail, final, final_fail, ready_oplan3, total_programs = result
            finished = ready_oplan3 + final
            # try:
            #     ready_index = (finished * 100) / total_programs
            # except Exception as e:
            #     print(e)
            #     ready_index = 'fail'
            # if ready_index == 'fail':
            #     color = ''
            if no_material:
                color = 'btn-outline-danger'
            elif total_programs-finished == 0:
                color = 'btn-outline-success'
            else:
                color = 'btn-outline-warning'

            return {
                'no_material': no_material, 'not_ready': not_ready, 'fix': fix, 'fix_ready': fix_ready, 'ready': ready,
                'otk': otk, 'otk_fail': otk_fail, 'final': final, 'final_fail': final_fail, 'ready_oplan3': ready_oplan3,
                'total_programs': total_programs, 'color': color
            }
        return {'status': 'error', 'message': 'empty list'}

def calc_prev_month(cal_year, cal_month):
    if cal_month > 1:
        prev_month = cal_month - 1
        prev_year = cal_year
    else:
        prev_month = 12
        prev_year = cal_year - 1
    return prev_year, prev_month

def calc_next_month(cal_year, cal_month):
    if cal_month < 12:
        next_month = cal_month + 1
        next_year = cal_year
    else:
        next_month = 1
        next_year = cal_year + 1
    return next_year, next_month