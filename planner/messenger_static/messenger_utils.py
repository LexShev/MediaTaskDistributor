from django.db import connections

from messenger_static.models import Notification
from planner.settings import OPLAN_DB, PLANNER_DB


def unique_program_id():
    with connections[PLANNER_DB].cursor() as cursor:
        query = f'SELECT DISTINCT [program_id] FROM [{PLANNER_DB}].[dbo].[messenger_static_message]'
        cursor.execute(query)
        programs = cursor.fetchall()
        if programs:
            return [program[0] for program in programs]

def all_messages(worker_id):
    with connections[PLANNER_DB].cursor() as cursor:
        columns = 'program_id', 'message', 'timestamp', 'Progs_name', 'Progs_production_year', 'read'
        query = f'''
        WITH LatestPrograms AS (
            SELECT TOP (50)
                m.[program_id]
            FROM 
                [{PLANNER_DB}].[dbo].[messenger_static_message] m
            GROUP BY 
                m.[program_id]
            ORDER BY 
                MAX(m.[timestamp]) DESC
        )

        SELECT
            m.[program_id],
            m.[message],
            m.[timestamp],
            Progs.[name],
            Progs.[production_year],
        	CASE 
                WHEN v.[message_id] IS NOT NULL THEN CAST(1 AS BIT)
                ELSE CAST(0 AS BIT)
            END AS [read]
        FROM 
            [{PLANNER_DB}].[dbo].[messenger_static_message] AS m
        LEFT JOIN [{PLANNER_DB}].[dbo].[messenger_static_messageviews] AS v
            ON m.[message_id] = v.[message_id] AND v.[worker_id] = {worker_id}
        LEFT JOIN [{OPLAN_DB}].[dbo].[program] AS Progs
            ON m.[program_id] = Progs.[program_id]
        WHERE m.[program_id] IN (SELECT [program_id] FROM LatestPrograms)
        ORDER BY
            m.[timestamp]
            DESC;
        '''
        # m.[program_id]
        cursor.execute(query)
        messages = cursor.fetchall()
        if messages:
            message_list = [dict(zip(columns, message)) for message in messages]
            message_sorted = {}
            for message in message_list:
                program_id = message.get('program_id')
                if program_id not in message_sorted:
                    message_sorted[program_id] = {
                        'messages': [],
                        'Progs_name': message.get('Progs_name'),
                        'Progs_production_year': message.get('Progs_production_year'),
                        'cur_unread': 0
                    }
                message_sorted[program_id]['messages'].append(message)
                if not message['read']:
                    message_sorted[program_id]['cur_unread'] += 1
            return message_sorted


def show_messages(program_id):
    with connections[PLANNER_DB].cursor() as cursor:
        columns = ('m_message_id', 'm_owner', 'm_program_id', 'm_message', 'm_file_path', 'Progs_name', 'Progs_production_year', 'm_timestamp')

        query = f'''
        SELECT m.[message_id], m.[owner], m.[program_id], m.[message], m.[file_path], Progs.[name], Progs.[production_year], m.[timestamp]
        FROM [{PLANNER_DB}].[dbo].[messenger_static_message] AS m
        LEFT JOIN [{OPLAN_DB}].[dbo].[program] AS Progs
            ON m.[program_id] = Progs.[program_id]
        WHERE m.[program_id] = {program_id}
        ORDER BY [timestamp]
        '''
        cursor.execute(query)
        messages = cursor.fetchall()
        if messages:
            message_list = []
            for message in messages:
                temp_dict = {}
                for key, val in zip(columns, message):
                    temp_dict[key] = val
                    file_path = temp_dict.get('m_file_path')
                temp_dict['file_type'] = file_type(file_path)
                message_list.append(temp_dict)
            return message_list

def file_type(file_path):
    if file_path:
        ext = file_path.split('.')[-1].lower()
        if ext in ['jpg', 'jpeg', 'png', 'gif']:
            return 'image'
        elif ext in ['mp4', 'mov', 'avi']:
            return 'video'
        elif ext in ['mp3', 'wav', 'aac', 'ac3']:
            return 'audio'
        else:
            return 'document'
    return None

def show_viewed_messages(program_id, worker_id):
    with connections[PLANNER_DB].cursor() as cursor:
        query = f'''
        SELECT [message_id]
        FROM [{PLANNER_DB}].[dbo].[messenger_static_messageviews]
        WHERE [worker_id] = {worker_id}
        AND [message_id] IN 
        (SELECT [message_id] FROM [{PLANNER_DB}].[dbo].[messenger_static_message] WHERE [program_id] = {program_id})'''
        cursor.execute(query)
        viewed_messages = cursor.fetchall()
        if viewed_messages:
            return [message_id[0] for message_id in viewed_messages]

def insert_views(program_id_list):
    with connections[PLANNER_DB].cursor() as cursor:
        query = f'''
        INSERT INTO [{PLANNER_DB}].[dbo].[messenger_static_messageviews]
        ([message_id], [worker_id])
        VALUES
        (%s, %s);
        '''
        cursor.executemany(query, program_id_list)
        return cursor.rowcount

def create_notification(data):
    try:
        Notification.objects.create(
            sender=data.get('sender'), recipient=data.get('recipient'), program_id=data.get('program_id'),
            message=data.get('message'), comment=data.get('comment')
        )
        return 'success'
    except Exception as e:
        print(e)
        return 'error'

def find_worker_id(name):
    if name:
        with connections[OPLAN_DB].cursor() as cursor:
            query = f'SELECT [id] FROM [{PLANNER_DB}].[dbo].[auth_user] WHERE [username] = %s'
            cursor.execute(query, (name,))
            worker = cursor.fetchone()
            if worker:
                return worker[0]
            else:
                return -1
    else:
        return -1
