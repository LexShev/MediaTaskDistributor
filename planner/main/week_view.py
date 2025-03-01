import datetime

from .db_connection import *


def weekday(date):
    return datetime.datetime.strptime(date, '%Y-%m-%d').weekday()

def repeat_index_search(material_list, temp_dict):
    for num, program in enumerate(material_list):
        if temp_dict['Progs_parent_id'] == program['Progs_parent_id']:
            return num

def week_material_list():
    material_list_sql, django_columns = planner_material_list()
    # material_list = []
    # mat_list_1, mat_list_2, mat_list_3, mat_list_4, mat_list_5, mat_list_6, mat_list_7 = [], [], [], [], [], [], []
    mat_list = [[], [], [], [], [], [], []]
    for program_info in material_list_sql:
        if not program_info:
            continue
        temp_dict = dict(zip(django_columns, program_info))
        day_num = temp_dict['Task_work_date'].weekday()
        if temp_dict['Progs_program_type_id'] in (4, 8, 12):
            repeat_index = repeat_index_search(mat_list[day_num], temp_dict)
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
                # material_list.append(program_info_dict)
                mat_list[day_num].append(program_info_dict)
                # if weekday(temp_dict['Task_work_date']) == 1:
                #     mat_list_1.append(program_info_dict)
                # elif weekday(temp_dict['Task_work_date']) == 2:
                #     mat_list_2.append(program_info_dict)
                # elif weekday(temp_dict['Task_work_date']) == 3:
                #     mat_list_3.append(program_info_dict)
                # elif weekday(temp_dict['Task_work_date']) == 4:
                #     mat_list_4.append(program_info_dict)
                # elif weekday(temp_dict['Task_work_date']) == 5:
                #     mat_list_5.append(program_info_dict)
                # elif weekday(temp_dict['Task_work_date']) == 6:
                #     mat_list_6.append(program_info_dict)
                # elif weekday(temp_dict['Task_work_date']) == 7:
                #     mat_list_7.append(program_info_dict)

            else:
                mat_list[day_num][repeat_index]['episode'].append(
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
            mat_list[day_num].append(program_info_dict)
    for mat in mat_list:
        print('mat', mat)
    return mat_list
