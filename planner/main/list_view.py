from .db_connection import *


def convert_fr_to_tf(frames, fps=25):
    sec = frames/fps
    hh = int(sec // 3600)
    mm = int((sec % 3600) // 60)
    ss = int((sec % 3600) % 60 // 1)
    ff = int(sec % 1 * fps)
    tf = f'{hh:02}:{mm:02}:{ss:02}.{ff:03}'
    return tf

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
        engineer_id, engineer, status, work_date = planner_task_list(program_id)
        if not engineer_id and not engineer:
            engineer_id, engineer = oplan3_engineer(program_id)
            status, work_date = 'ready', None
        if temp_dict['Progs_program_type_id'] in (4, 8, 12):
            repeat_index = repeat_index_search(material_list, temp_dict)
            if not repeat_index and repeat_index != 0:
                program_info_dict = {
                    'Progs_parent_id': temp_dict['Progs_parent_id'],
                    'Progs_AnonsCaption': temp_dict['Progs_AnonsCaption'],
                    'Progs_production_year': temp_dict['Progs_production_year'],
                    'color': select_channel_color(temp_dict['Task_sched_id']),
                    'Task_sched_id': select_channel_color(temp_dict['Task_sched_id']),
                    'Sched_schedule_name': temp_dict['Sched_schedule_name'],
                    'type': 'season',
                    'episode': [
                        {'Progs_program_id': temp_dict['Progs_program_id'],
                         'Progs_name': temp_dict['Progs_name'],
                         'Progs_episode_num': temp_dict['Progs_episode_num'],
                         'Progs_duration': temp_dict['Progs_duration'],
                         'TaskInf_work_date': work_date,
                         'Task_sched_date': temp_dict['Task_sched_date'],
                         'status': status,
                         'engineer_id': engineer_id,
                         'engineer': engineer}
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
                    'Task_sched_date': temp_dict['Task_sched_date'],
                    'status': status,
                    'engineer_id': engineer_id,
                    'engineer': engineer})
                program_id_list.append(program_id)
        if not temp_dict['Progs_program_type_id'] in (4, 8, 12):
            program_info_dict = {
                'Progs_program_id': temp_dict['Progs_program_id'],
                'Progs_parent_id': temp_dict['Progs_parent_id'],
                'Progs_name': temp_dict['Progs_name'],
                'Progs_production_year': temp_dict['Progs_production_year'],
                'Progs_duration': temp_dict['Progs_duration'],
                'TaskInf_work_date': work_date,
                'color': select_channel_color(temp_dict['Task_sched_id']),
                'Task_sched_id': select_channel_color(temp_dict['Task_sched_id']),
                'Sched_schedule_name': temp_dict['Sched_schedule_name'],
                'Task_sched_date': temp_dict['Task_sched_date'],
                'type': 'film',
                'status': status,
                'engineer_id': engineer_id,
                'engineer': engineer}
            program_id_list.append(program_id)
            material_list.append(program_info_dict)
    return material_list

def list_material_list(channels, engineer_id, material_type, dates, task_status):
    material_list_sql, django_columns = planner_material_list(channels, engineer_id, material_type, dates, task_status)
    material_list = []
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
        if temp_dict['Progs_program_type_id'] in (4, 8, 12):
            repeat_index = repeat_index_search(material_list, temp_dict)
            if not repeat_index and repeat_index != 0:
                program_info_dict = {
                    'Progs_parent_id': temp_dict.get('Progs_parent_id'),
                    'Progs_AnonsCaption': parent_name(temp_dict.get('Progs_parent_id')),
                    'Progs_production_year': temp_dict.get('Progs_production_year'),
                    'color': select_channel_color(temp_dict.get('Task_sched_id')),
                    'Task_sched_id': temp_dict.get('Task_sched_id'),
                    'Sched_schedule_name': temp_dict.get('Sched_schedule_name'),
                    'type': 'season',
                    'episode': [
                        {'Progs_program_id': temp_dict.get('Progs_program_id'),
                         'Progs_name': temp_dict.get('Progs_name'),
                         'Progs_episode_num': temp_dict.get('Progs_episode_num'),
                         'Progs_duration': temp_dict.get('Progs_duration'),
                         'Adult_Name': temp_dict.get('Adult_Name'),
                         'TaskInf_work_date': temp_dict.get('Task_work_date'),
                         'Task_sched_date': temp_dict.get('Task_sched_date'),
                         'status': temp_dict.get('Task_task_status'),
                         'engineer_id': temp_dict.get('Task_engineer_id')
                         }
                    ]
                }
                material_list.append(program_info_dict)
                program_id_list.append(program_id)
            else:
                material_list[repeat_index]['episode'].append(
                    {'Progs_program_id': temp_dict.get('Progs_program_id'),
                    'Progs_name': temp_dict.get('Progs_name'),
                    'Progs_episode_num': temp_dict.get('Progs_episode_num'),
                    'Progs_duration': temp_dict.get('Progs_duration'),
                    'Adult_Name': temp_dict.get('Adult_Name'),
                    'TaskInf_work_date': temp_dict.get('Task_work_date'),
                    'Task_sched_date': temp_dict.get('Task_sched_date'),
                    'status': temp_dict.get('Task_task_status'),
                    'engineer_id': temp_dict.get('Task_engineer_id')
                    })
                program_id_list.append(program_id)
        if not temp_dict.get('Progs_program_type_id') in (4, 8, 12):
            program_info_dict = {
                'Progs_program_id': temp_dict.get('Progs_program_id'),
                'Progs_parent_id': temp_dict.get('Progs_parent_id'),
                'Progs_name': temp_dict.get('Progs_name'),
                'Progs_production_year': temp_dict.get('Progs_production_year'),
                'Progs_duration': temp_dict.get('Progs_duration'),
                'Adult_Name': temp_dict.get('Adult_Name'),
                'TaskInf_work_date': temp_dict.get('Task_work_date'),
                'color': select_channel_color(temp_dict.get('Task_sched_id')),
                'Task_sched_id': temp_dict.get('Task_sched_id'),
                'Sched_schedule_name': temp_dict.get('Sched_schedule_name'),
                'Task_sched_date': temp_dict.get('Task_sched_date'),
                'type': 'film',
                'status': temp_dict.get('Task_task_status'),
                'engineer_id': temp_dict.get('Task_engineer_id')
                }
            material_list.append(program_info_dict)
            program_id_list.append(program_id)
    return material_list

