from .db_connection import *


def convert_fr_to_tf(frames, fps=25):
    sec = frames/fps
    hh = int(sec // 3600)
    mm = int((sec % 3600) // 60)
    ss = int((sec % 3600) % 60 // 1)
    ff = int(sec % 1 * fps)
    tf = f'{hh:02}:{mm:02}:{ss:02}.{ff:03}'
    return tf

def repeat_index_search(material_list, temp_dict):
    for num, program in enumerate(material_list):
        if temp_dict['Progs_parent_id'] == program['Progs_parent_id']:
            return num

def make_full_material_list():
    material_list_sql, django_columns = oplan_material_list(program_type=(4, 5, 6, 7, 8, 10, 11, 12, 16, 17, 18, 19, 20))
    material_list = []
    program_id_list = []
    for program_info in material_list_sql:
        if not program_info:
            continue
        program_id = program_info[0]
        if program_id in program_id_list:
            continue
        temp_dict = dict(zip(django_columns, program_info))
        worker_id, worker, status, work_date = planner_task_list(program_id)
        if not worker_id and not worker:
            worker_id, worker = oplan3_cenz_worker(program_id)
            status, work_date = 'ready', None
        if temp_dict['Progs_program_type_id'] in (4, 8, 12):
            repeat_index = repeat_index_search(material_list, temp_dict)
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
                         'TaskInf_work_date': work_date,
                         'Sched_schedule_name': temp_dict['Sched_schedule_name'],
                         'SchedDay_day_date': temp_dict['SchedDay_day_date'],
                         'status': status,
                         'worker_id': worker_id,
                         'worker': worker}
                    ]
                }
                program_id_list.append(program_id)
                material_list.append(program_info_dict)
            else:
                material_list[repeat_index]['episode'].append(
                    {'Progs_program_id': temp_dict['Progs_program_id'],
                    'Progs_name': temp_dict['Progs_name'],
                    'Progs_episode_num': temp_dict['Progs_episode_num'],
                    'Progs_duration': temp_dict['Progs_duration'],
                    'TaskInf_work_date': work_date,
                    'Sched_schedule_name': temp_dict['Sched_schedule_name'],
                    'SchedDay_day_date': temp_dict['SchedDay_day_date'],
                    'status': status,
                    'worker_id': worker_id,
                    'worker': worker})
                program_id_list.append(program_id)
        if not temp_dict['Progs_program_type_id'] in (4, 8, 12):
            program_info_dict = {
                'Progs_program_id': temp_dict['Progs_program_id'],
                'Progs_parent_id': temp_dict['Progs_parent_id'],
                'Progs_name': temp_dict['Progs_name'],
                'Progs_production_year': temp_dict['Progs_production_year'],
                'Progs_duration': temp_dict['Progs_duration'],
                'TaskInf_work_date': work_date,
                'Sched_schedule_name': temp_dict['Sched_schedule_name'],
                'SchedDay_day_date': temp_dict['SchedDay_day_date'],
                'type': 'film',
                'status': status,
                'worker_id': worker_id,
                'worker': worker}
            program_id_list.append(program_id)
            material_list.append(program_info_dict)
    return material_list

def list_material_list(worker_id, dates):
    material_list_sql, django_columns = planner_material_list(worker_id, dates)
    material_list = []
    program_id_list = []
    for program_info in material_list_sql:
        if not program_info:
            continue
        program_id = program_info[0]
        if program_id in program_id_list:
            continue
        temp_dict = dict(zip(django_columns, program_info))
        if temp_dict['Progs_program_type_id'] in (4, 8, 12):
            repeat_index = repeat_index_search(material_list, temp_dict)
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
                         'TaskInf_work_date': temp_dict['Task_work_date'],
                         'Sched_schedule_name': temp_dict['Sched_schedule_name'],
                         'SchedDay_day_date': temp_dict['SchedDay_day_date'],
                         'status': temp_dict['Task_task_status'],
                         'worker_id': temp_dict['Task_worker_id'],
                         'worker': temp_dict['Task_worker']}
                    ]
                }
                material_list.append(program_info_dict)
                program_id_list.append(program_id)
            else:
                material_list[repeat_index]['episode'].append(
                    {'Progs_program_id': temp_dict['Progs_program_id'],
                    'Progs_name': temp_dict['Progs_name'],
                    'Progs_episode_num': temp_dict['Progs_episode_num'],
                    'Progs_duration': temp_dict['Progs_duration'],
                    'TaskInf_work_date': temp_dict['Task_work_date'],
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
                'TaskInf_work_date': temp_dict['Task_work_date'],
                'Sched_schedule_name': temp_dict['Sched_schedule_name'],
                'SchedDay_day_date': temp_dict['SchedDay_day_date'],
                'type': 'film',
                'status': temp_dict['Task_task_status'],
                'worker_id': temp_dict['Task_worker_id'],
                'worker': temp_dict['Task_worker']}
            material_list.append(program_info_dict)
            program_id_list.append(program_id)
    return material_list

