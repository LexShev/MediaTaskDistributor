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
            COUNT(DISTINCT CASE WHEN Task.[task_status] = 'no_material' THEN Progs.[program_id] END) AS no_material,
            COUNT(DISTINCT CASE WHEN Task.[task_status] = 'not_ready' THEN Progs.[program_id] END) AS not_ready,
            COUNT(DISTINCT CASE WHEN Task.[task_status] = 'fix' THEN Progs.[program_id] END) AS fix,
            COUNT(DISTINCT CASE WHEN Task.[task_status] = 'fix_ready' THEN Progs.[program_id] END) AS fix_ready,
            COUNT(DISTINCT CASE WHEN Task.[task_status] = 'ready' THEN Progs.[program_id] END) AS ready,
            COUNT(DISTINCT CASE WHEN Task.[task_status] = 'otk' THEN Progs.[program_id] END) AS otk,
            COUNT(DISTINCT CASE WHEN Task.[task_status] = 'otk_fail' THEN Progs.[program_id] END) AS otk_fail,
            COUNT(DISTINCT CASE WHEN Task.[task_status] = 'final' THEN Progs.[program_id] END) AS final,
            COUNT(DISTINCT CASE WHEN Task.[task_status] = 'final_fail' THEN Progs.[program_id] END) AS final_fail,
            COUNT(DISTINCT CASE WHEN CustField.has_custom_field = 1 AND Task.[program_id] IS NULL THEN Progs.[program_id] END) AS ready_oplan3,
            COUNT(DISTINCT CASE WHEN Task.[program_id] IS NULL AND CustField.has_custom_field = 0 THEN Progs.[program_id] END) AS not_distr,
            COUNT(DISTINCT Progs.[program_id]) AS total_programs
        FROM [oplan3].[dbo].[program] AS Progs
        JOIN [oplan3].[dbo].[scheduled_program] AS SchedProg
            ON Progs.[program_id] = SchedProg.[program_id]
        JOIN [oplan3].[dbo].[schedule_day] AS SchedDay
            ON SchedProg.[schedule_day_id] = SchedDay.[schedule_day_id]
        JOIN [oplan3].[dbo].[schedule] AS Sched
            ON SchedDay.[schedule_id] = Sched.[schedule_id]
        LEFT JOIN [planner].[dbo].[task_list] AS Task
            ON Progs.[program_id] = Task.[program_id]
        OUTER APPLY (
            SELECT CASE WHEN EXISTS (
                SELECT 1 FROM [oplan3].[dbo].[ProgramCustomFieldValues] 
                WHERE ObjectId = Progs.[program_id] 
                AND ProgramCustomFieldId IN (7, 14, 15)
            ) THEN 1 ELSE 0 END as has_custom_field
        ) AS CustField
        WHERE SchedDay.[day_date] = @current_date
        AND Progs.[program_id] > 0
        AND Progs.[deleted] = 0
        AND Progs.[DeletedIncludeParent] = 0
        AND Progs.[program_type_id] IN (4, 5, 6, 7, 8, 10, 11, 12, 16, 19, 20)
        AND SchedProg.[Deleted] = 0
        {sched_sort(schedule_id)}
        '''
        , (current_date,))
        result = cursor.fetchone()
        if result:
            no_material, not_ready, fix, fix_ready, ready, otk, otk_fail, final, final_fail, ready_oplan3, not_distr, total_programs = result
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
            elif not_distr:
                color = 'btn-outline-warning'
            elif not total_programs:
                color = 'btn-outline-secondary'
            elif (total_programs - finished) == 0:
                color = 'btn-outline-success'
            else:
                color = 'btn-outline-orange'

            return {
                'no_material': no_material, 'not_ready': not_ready, 'fix': fix, 'fix_ready': fix_ready, 'ready': ready,
                'otk': otk, 'otk_fail': otk_fail, 'final': final, 'final_fail': final_fail, 'ready_oplan3': ready_oplan3,
                'not_distr': not_distr, 'total_programs': total_programs, 'color': color
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