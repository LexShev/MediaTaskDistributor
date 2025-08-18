from datetime import date, timedelta

from .db_connection import *

#
# def week_num(date):
#     return datetime.strptime(date, '%Y-%m-%d').weekday()

def select_channel_color(schedule_id):
    color_dict = {
        3: '#dc3545', # Крепкое
        5: '#0d6efd', # Планета дети
        6: '#ffc107', # Мировой сериал
        7: '#fd7e14', # Мужской сериал
        8: '#0dcaf0', # Наше детство
        9: '#d63384', # Романтичный сериал
        10: '#198754', # Наше родное кино
        11: '#6f42c1', # Семейное кино
        12: '#20c997', # Советское родное кино
        20: '#6610f2'} # Кино +
    return color_dict.get(schedule_id)

def repeat_index_search(material_list, parent_id):
    for num, program in enumerate(material_list):
        if parent_id == program.get('Progs_parent_id'):
            return num

def week_material_list(schedules_id, engineer_id, material_type, task_status, work_year, work_week, user_order, order_type):
    start_day = date.fromisocalendar(work_year, work_week, 1)
    print('start_day', start_day)
    end_day = start_day + timedelta(6)

    prev_mon = start_day - timedelta(7)
    next_mon = start_day + timedelta(7)

    prev_week = prev_mon.isocalendar().week
    next_week = next_mon.isocalendar().week
    prev_year = prev_mon.isocalendar().year
    next_year = next_mon.isocalendar().year

    # dates = tuple((start_day + timedelta(day_num)).strftime('%Y-%m-%d') for day_num in range(7))
    material_list_sql, django_columns = planner_material_list(
        schedules_id, engineer_id, material_type, (start_day, end_day), task_status, user_order, order_type
    )

    service_dict = {'start_day': start_day, 'prev_year': prev_year, 'prev_week': prev_week,
                    'next_year': next_year, 'next_week': next_week, 'work_year': work_year,
                    'work_week': work_week}
    material_list = [
        [{'day_num': 1, 'date': start_day + timedelta(0), 'weekday': 'Понедельник'}],
        [{'day_num': 2, 'date': start_day + timedelta(1), 'weekday': 'Вторник'}],
        [{'day_num': 3, 'date': start_day + timedelta(2), 'weekday': 'Среда'}],
        [{'day_num': 4, 'date': start_day + timedelta(3), 'weekday': 'Четверг'}],
        [{'day_num': 5, 'date': start_day + timedelta(4), 'weekday': 'Пятница'}],
        [{'day_num': 6, 'date': start_day + timedelta(5), 'weekday': 'Суббота'}],
        [{'day_num': 7, 'date': start_day + timedelta(6), 'weekday': 'Воскресенье'}]
    ]
    program_id_list = []
    for program_info in material_list_sql:
        if not program_info:
            continue
        program_id = program_info[0]
        if program_id in program_id_list:
            continue
        temp_dict = dict(zip(django_columns, program_info))
        if not temp_dict.get('Adult_Name'):
            temp_dict['Adult_Name'] = parent_adult_name(temp_dict.get('Progs_parent_id'))
        day_num = temp_dict['Task_work_date'].weekday()
        if temp_dict['Progs_program_type_id'] in (4, 8, 12):
            repeat_index = repeat_index_search(material_list[day_num], temp_dict.get('Progs_parent_id'))
            if not repeat_index and repeat_index != 0:
                program_info_dict = {
                    'Progs_parent_id': temp_dict.get('Progs_parent_id'),
                    'Progs_AnonsCaption': parent_name(temp_dict.get('Progs_parent_id')),
                    'Progs_production_year': temp_dict.get('Progs_production_year'),
                    'color': select_channel_color(temp_dict.get('Task_sched_id')),
                    'Task_sched_id': temp_dict.get('Task_sched_id'),
                    'Sched_schedule_id': temp_dict.get('Sched_schedule_id'),
                    'type': 'season',
                    'episode': [
                        {'Progs_program_id': temp_dict.get('Progs_program_id'),
                         'Progs_name': temp_dict.get('Progs_name'),
                         'Progs_episode_num': temp_dict.get('Progs_episode_num'),
                         'Progs_duration': temp_dict.get('Progs_duration'),
                         'Adult_Name': temp_dict.get('Adult_Name'),
                         'Task_work_date': temp_dict.get('Task_work_date'),
                         'Task_sched_date': temp_dict.get('Task_sched_date'),
                         'status': temp_dict.get('Task_task_status'),
                         'Task_engineer_id': temp_dict.get('Task_engineer_id')
                         }
                    ]
                }
                material_list[day_num].append(program_info_dict)
                program_id_list.append(program_id)
            else:
                material_list[day_num][repeat_index]['episode'].append(
                    {'Progs_program_id': temp_dict.get('Progs_program_id'),
                    'Progs_name': temp_dict.get('Progs_name'),
                    'Progs_episode_num': temp_dict.get('Progs_episode_num'),
                    'Progs_duration': temp_dict.get('Progs_duration'),
                    'Adult_Name': temp_dict.get('Adult_Name'),
                    'Task_work_date': temp_dict.get('Task_work_date'),
                    'Task_sched_date': temp_dict.get('Task_sched_date'),
                    'status': temp_dict.get('Task_task_status'),
                    'Task_engineer_id': temp_dict.get('Task_engineer_id')
                     })
                program_id_list.append(program_id)
        if not temp_dict['Progs_program_type_id'] in (4, 8, 12):
            program_info_dict = {
                'Progs_program_id': temp_dict.get('Progs_program_id'),
                'Progs_parent_id': temp_dict.get('Progs_parent_id'),
                'Progs_name': temp_dict.get('Progs_name'),
                'Progs_production_year': temp_dict.get('Progs_production_year'),
                'Progs_duration': temp_dict.get('Progs_duration'),
                'Adult_Name': temp_dict.get('Adult_Name'),
                'Task_work_date': temp_dict.get('Task_work_date'),
                'color': select_channel_color(temp_dict.get('Task_sched_id')),
                'Task_sched_id': temp_dict.get('Task_sched_id'),
                'Sched_schedule_id': temp_dict.get('Sched_schedule_id'),
                'Task_sched_date': temp_dict.get('Task_sched_date'),
                'type': 'film',
                'status': temp_dict.get('Task_task_status'),
                'Task_engineer_id': temp_dict.get('Task_engineer_id')
            }
            material_list[day_num].append(program_info_dict)
            program_id_list.append(program_id)
    return material_list, service_dict

