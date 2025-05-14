from django.db import connections


def unique_program_id():
    with connections['planner'].cursor() as cursor:
        query = 'SELECT DISTINCT [program_id] FROM [planner].[dbo].[messenger_static_message]'
        cursor.execute(query)
        programs = cursor.fetchall()
        if programs:
            return [program[0] for program in programs]


def show_messages(program_id, worker_id):
    messages_dict, viewed_messages_list = [], []
    with connections['planner'].cursor() as cursor:
        columns = ('message_id', 'owner', 'program_id', 'message', 'file_path', 'timestamp')
        sql_columns = ', '.join(f'[{col}]' for col in columns)
        query_01 = f'''
        SELECT {sql_columns}
        FROM [planner].[dbo].[messenger_static_message]
        WHERE [program_id] = {program_id}
        ORDER BY [timestamp]
        '''
        cursor.execute(query_01)
        messages = cursor.fetchall()
        if messages:
            messages_dict = [dict(zip(columns, message)) for message in messages]

        query_02 = f'''
        SELECT [message_id]
        FROM [planner].[dbo].[messenger_static_messageviews]
        WHERE [worker_id] = {worker_id}
        AND [message_id] IN 
        (SELECT [message_id] FROM [planner].[dbo].[messenger_static_message] WHERE [program_id] = {program_id})'''
        cursor.execute(query_02)
        viewed_messages = cursor.fetchall()
        if viewed_messages:
            viewed_messages_list = [message_id[0] for message_id in viewed_messages]
    return messages_dict, viewed_messages_list
