import datetime

from .db_connection import *

#
# def week_num(date):
#     return datetime.datetime.strptime(date, '%Y-%m-%d').weekday()

def repeat_index_search(material_list, temp_dict):
    for num, program in enumerate(material_list):
        if temp_dict.get('Progs_parent_id') == program.get('Progs_parent_id'):
            return num

def week_material_list(work_year, work_week):
    start_day = datetime.date.fromisocalendar(work_year, work_week, 1)

    prev_mon = start_day - datetime.timedelta(7)
    next_mon = start_day + datetime.timedelta(7)

    prev_week = prev_mon.isocalendar().week
    next_week = next_mon.isocalendar().week
    prev_year = prev_mon.isocalendar().year
    next_year = next_mon.isocalendar().year

    dates = tuple((start_day + datetime.timedelta(day_num)).strftime('%Y-%m-%d') for day_num in range(7))
    material_list_sql, django_columns = planner_material_list(dates)

    service_dict = {'start_day': start_day, 'prev_year': prev_year, 'prev_week': prev_week,
                    'next_year': next_year, 'next_week': next_week, 'work_year': work_year,
                    'work_week': work_week}
    material_list = [
        [{'day_num': 1, 'date': start_day + datetime.timedelta(0), 'weekday': 'Понедельник'}],
        [{'day_num': 2, 'date': start_day + datetime.timedelta(1), 'weekday': 'Вторник'}],
        [{'day_num': 3, 'date': start_day + datetime.timedelta(2), 'weekday': 'Среда'}],
        [{'day_num': 4, 'date': start_day + datetime.timedelta(3), 'weekday': 'Четверг'}],
        [{'day_num': 5, 'date': start_day + datetime.timedelta(4), 'weekday': 'Пятница'}],
        [{'day_num': 6, 'date': start_day + datetime.timedelta(5), 'weekday': 'Суббота'}],
        [{'day_num': 7, 'date': start_day + datetime.timedelta(6), 'weekday': 'Воскресенье'}]
    ]
    program_id_list = []
    for program_info in material_list_sql:
        if not program_info:
            continue
        program_id = program_info[0]
        if program_id in program_id_list:
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
                program_id_list.append(program_id)
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
                program_id_list.append(program_id)
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
            program_id_list.append(program_id)
    return {'week_material_list': material_list, 'service_dict': service_dict}
