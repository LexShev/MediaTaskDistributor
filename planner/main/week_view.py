import datetime

from .db_connection import *


def weekday(date):
    return datetime.datetime.strptime(date, '%Y-%m-%d').weekday()

def repeat_index_search(material_list, temp_dict):
    for num, program in enumerate(material_list):
        if temp_dict.get('Progs_parent_id') == program.get('Progs_parent_id'):
            return num

def week_material_list(start_day):
    start_day = datetime.datetime.strptime(start_day, '%Y-%m-%d')
    prev_week_day = start_day - datetime.timedelta(7)
    next_week_day = start_day + datetime.timedelta(7)
    dates = tuple((start_day + datetime.timedelta(day_num)).strftime('%Y-%m-%d') for day_num in range(7))
    # week_num = start_day.isocalendar().week
    material_list_sql, django_columns = planner_material_list(dates)
    week_dates = f'{dates[0]} - {dates[-1]}'
    service_dict = {'start_day': start_day, 'week_dates': week_dates, 'prev_week_day': prev_week_day, 'next_week_day': next_week_day}
    material_list = [
        [{'day_num': 1, 'date': start_day + datetime.timedelta(0), 'weekday': 'Пн'}],
        [{'day_num': 2, 'date': start_day + datetime.timedelta(1), 'weekday': 'Вт'}],
        [{'day_num': 3, 'date': start_day + datetime.timedelta(2), 'weekday': 'Ср'}],
        [{'day_num': 4, 'date': start_day + datetime.timedelta(3), 'weekday': 'Чт'}],
        [{'day_num': 5, 'date': start_day + datetime.timedelta(4), 'weekday': 'Пт'}],
        [{'day_num': 6, 'date': start_day + datetime.timedelta(5), 'weekday': 'Сб'}],
        [{'day_num': 7, 'date': start_day + datetime.timedelta(6), 'weekday': 'Вс'}]
    ]
    for program_info in material_list_sql:
        if not program_info:
            continue
        temp_dict = dict(zip(django_columns, program_info))
        day_num = temp_dict['Task_work_date'].weekday()
        if temp_dict['Progs_program_type_id'] in (4, 8, 12):
            repeat_index = repeat_index_search(material_list[day_num], temp_dict)
            if not repeat_index and repeat_index != 0:
                program_info_dict = {
                    'Progs_parent_id': temp_dict['Progs_parent_id'],
                    'Progs_AnonsCaption': temp_dict['Progs_AnonsCaption'],
                    'Progs_production_year': temp_dict['Progs_production_year'],
                    'type': 'season',
                    'episode': [
                        {'Progs_program_id': temp_dict['Progs_program_id'],
                         'Progs_name': temp_dict['Progs_name'],
                         'Progs_episode_num': temp_dict['Progs_episode_num'],
                         'Progs_duration': temp_dict['Progs_duration'],
                         'Task_work_date': temp_dict['Task_work_date'],
                         'Sched_schedule_name': temp_dict['Sched_schedule_name'],
                         'SchedDay_day_date': temp_dict['SchedDay_day_date'],
                         'status': temp_dict['Task_task_status'],
                         'worker_id': temp_dict['Task_worker_id'],
                         'worker': temp_dict['Task_worker']}
                    ]
                }
                material_list[day_num].append(program_info_dict)
            else:
                material_list[day_num][repeat_index]['episode'].append(
                    {'Progs_program_id': temp_dict['Progs_program_id'],
                    'Progs_name': temp_dict['Progs_name'],
                    'Progs_episode_num': temp_dict['Progs_episode_num'],
                    'Progs_duration': temp_dict['Progs_duration'],
                    'Task_work_date': temp_dict['Task_work_date'],
                    'Sched_schedule_name': temp_dict['Sched_schedule_name'],
                    'SchedDay_day_date': temp_dict['SchedDay_day_date'],
                    'status': temp_dict['Task_task_status'],
                    'worker_id': temp_dict['Task_worker_id'],
                    'worker': temp_dict['Task_worker']})
        if not temp_dict['Progs_program_type_id'] in (4, 8, 12):
            program_info_dict = {
                'Progs_program_id': temp_dict['Progs_program_id'],
                'Progs_parent_id': temp_dict['Progs_parent_id'],
                'Progs_name': temp_dict['Progs_name'],
                'Progs_production_year': temp_dict['Progs_production_year'],
                'Progs_duration': temp_dict['Progs_duration'],
                'Task_work_date': temp_dict['Task_work_date'],
                'Sched_schedule_name': temp_dict['Sched_schedule_name'],
                'SchedDay_day_date': temp_dict['SchedDay_day_date'],
                'type': 'film',
                'status': temp_dict['Task_task_status'],
                'worker_id': temp_dict['Task_worker_id'],
                'worker': temp_dict['Task_worker']}
            material_list[day_num].append(program_info_dict)
    return {'week_material_list': material_list, 'service_dict': service_dict}
