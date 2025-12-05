from datetime import date, datetime

from django.db import connections
from django.http import JsonResponse

from planner.settings import OPLAN_DB

def check_schedule(schedule_id):
    try:
        if not schedule_id:
            return 'AND [schedule_id] IN (3, 5, 6, 7, 8, 9, 10, 11, 12, 20)'
        return f'AND [schedule_id] = {schedule_id}'
    except Exception as error:
        print(error)
        return 'AND [schedule_id] IN (3, 5, 6, 7, 8, 9, 10, 11, 12, 20)'

def check_date(schedule_date):
    today = date.today()
    if not schedule_date or schedule_date == '[]':
        return today, today
    try:
        return [datetime.strptime(str_date, '%d.%m.%Y') for str_date in schedule_date.split(' - ')]
    except Exception as error:
        print(error)
        return today, today

def get_schedule_days(field_dict):
    start_date, end_date = check_date(field_dict.get('schedule_date'))
    with connections[OPLAN_DB].cursor() as cursor:
        query = f"""
        SELECT 
            [schedule_day_id],
            [schedule_id],
            [day_date],
            [approved_for_broadcasting],
            [last_edit_user_id],
            [last_edit_time],
            [DayStatus],
            [AdvertImportDay],
            [PromoImportDay],
            [MusicImportDay],
            [AdvertListImportDay],
            [DayType]
        FROM [{OPLAN_DB}].[dbo].[schedule_day]
        WHERE [day_date] BETWEEN CONVERT(DATE, %s) AND CONVERT(DATE, %s)
        {check_schedule(field_dict.get('schedule_id'))}
        ORDER BY [day_date]
        """

        cursor.execute(query, (start_date, end_date))
        columns = [col[0] for col in cursor.description]
        results = []

        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))

        return results
