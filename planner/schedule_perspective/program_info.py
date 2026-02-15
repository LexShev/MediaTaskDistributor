from datetime import timedelta

from django.db import connections

from planner.settings import OPLAN_DB, PLANNER_DB


def get_program_info(start_date, schedule_id) -> dict:
    interval = 7
    program_dict = {start_date + timedelta(day): [] for day in range(interval)}
    try:

        with connections[PLANNER_DB].cursor() as cursor:
            columns = [('SchedDay', 'schedule_day_id'), ('SchedDay', 'schedule_id'),
                       ('SchedDay', 'approved_for_broadcasting'), ('SchedDay', 'day_date'),
                       ('SchedDay', 'last_edit_user_id'), ('SchedDay', 'last_edit_time'),
                       ('SchedDay', 'schedule_type'), ('SchedProg', 'name'), ('SchedProg', 'duration'),
                       ('SchedProg', 'index'), ('PlannerProg', 'name'), ('PlannerProg', 'original_name'),
                       ('PlannerProg', 'kinopoisk_id'), ('PlannerProg', 'oplan_program_id'),
                       ('OplanProg', 'name'), ('OplanProg', 'AnonsCaption')]

            sql_columns = ', '.join([f'{col}.[{val}]' for col, val in columns])
            django_columns = [f'{col}_{val}' for col, val in columns]
            query = f'''
            DECLARE @start_date DATE = %s
            SELECT {sql_columns}
            FROM [{PLANNER_DB}].[dbo].[schedule_day] AS SchedDay
            LEFT JOIN [{PLANNER_DB}].[dbo].scheduled_program AS SchedProg
                ON SchedDay.[schedule_day_id] = SchedProg.[schedule_day_id]
            LEFT JOIN [{PLANNER_DB}].[dbo].[program] AS PlannerProg
                ON SchedProg.[planner_program_id] = PlannerProg.[planner_program_id]
            LEFT JOIN [{OPLAN_DB}].[dbo].[program] AS OplanProg
                ON PlannerProg.[oplan_program_id] = OplanProg.[program_id]
            WHERE SchedDay.[day_date] BETWEEN @start_date AND DATEADD(DAY, %s, @start_date)
            AND SchedDay.[schedule_id] = %s
            ORDER BY SchedDay.[day_date], SchedProg.[index];
            '''
            cursor.execute(query, (start_date, interval, schedule_id))
            result = cursor.fetchall()
        search_list = [dict(zip(django_columns, task)) for task in result]
        for program in search_list:
            day_date = program.get('SchedDay_day_date')
            program_dict[day_date].append(program)
        print('date_list', program_dict)
        return program_dict
    except Exception as error:
        print(error)
        return program_dict

def update_schedule_info(schedule_id, oplan_program_id, from_container, to_container, old_index, new_index):
    try:
        with connections[PLANNER_DB].cursor() as cursor:
            query = f'''
            DECLARE @schedule_id INT = %s;  -- ID канала/плейлиста
            DECLARE @oplan_program_id INT = %s;
            DECLARE @day_date DATE = %s;
            DECLARE @scheduled_program_index INT = %s;
            
            DECLARE @planner_program_id INT;
            DECLARE @schedule_day_id INT;
            
            
            -- Табличные переменные для хранения OUTPUT значений
            DECLARE @ProgramOutput TABLE (planner_program_id INT);
            DECLARE @ScheduleDayOutput TABLE (schedule_day_id INT);
            
            -- Проверяем существование программы в planner
            IF NOT EXISTS (SELECT 1 FROM [planner].[dbo].[program] WHERE [oplan_program_id] = @oplan_program_id)
            BEGIN
                BEGIN TRANSACTION;
                
                BEGIN TRY
                    -- 1. Вставляем в program
                    INSERT INTO [planner].[dbo].[program] (
                        oplan_program_id,
                        name,
                        original_name,
                        episode_num,
                        production_year,
                        production_country,
                        actors,
                        directors,
                        duration,
                        program_type,
                        adult_type_id
                    )
                    OUTPUT INSERTED.planner_program_id INTO @ProgramOutput
                    SELECT 
                        @oplan_program_id,
                        name,
                        orig_name,
                        episode_num,
                        production_year,
                        production_country,
                        [Cast],
                        [Director],
                        duration,
                        program_type_id,
                        AdultTypeID
                    FROM [oplan3].[dbo].[program]
                    WHERE program_id = @oplan_program_id;
                    
                    SELECT @planner_program_id = planner_program_id FROM @ProgramOutput;
                    
                    COMMIT TRANSACTION;
                END TRY
                BEGIN CATCH
                    ROLLBACK TRANSACTION;
                    THROW;
                END CATCH
            END
            ELSE
            BEGIN
                -- Программа уже есть, получаем её ID
                SELECT @planner_program_id = planner_program_id 
                FROM [planner].[dbo].[program] 
                WHERE oplan_program_id = @oplan_program_id;
            END
            
            -- ============= ВАЖНАЯ ЧАСТЬ: GET OR CREATE для schedule_day =============
            -- Проверяем, существует ли уже запись для этого канала и даты
            SELECT @schedule_day_id = schedule_day_id 
            FROM [planner].[dbo].[schedule_day] 
            WHERE schedule_id = @schedule_id 
              AND day_date = @day_date;  -- сравниваем только дату, без времени
            
            -- Если записи нет - создаём
            IF @schedule_day_id IS NULL
            BEGIN
                INSERT INTO [planner].[dbo].[schedule_day] (
                    schedule_id,
                    day_date,
                    approved_for_broadcasting,
                    last_edit_user_id,
                    schedule_type
                )
                OUTPUT INSERTED.schedule_day_id INTO @ScheduleDayOutput
                VALUES (
                    @schedule_id, 
                    @day_date,
                    1, 
                    2, 
                    4
                );
                
                SELECT @schedule_day_id = schedule_day_id FROM @ScheduleDayOutput;
            END
            
            -- ============= ВСЕГДА создаём новую запись в scheduled_program =============
            -- (даже если программа уже есть в этот день - могут быть повторы)
            INSERT INTO [planner].[dbo].scheduled_program (
                schedule_day_id,
                planner_program_id,
                duration,
                name,
                last_edit_time,
                [index]
            )
            SELECT 
                @schedule_day_id,
                @planner_program_id,
                p.duration,
                p.name,
                GETDATE(),
                @scheduled_program_index
            FROM [oplan3].[dbo].[program] p
            WHERE p.program_id = @oplan_program_id;
            
            -- Показываем результат
            SELECT 
                @planner_program_id as planner_program_id,
                @schedule_day_id as schedule_day_id,
                (SELECT name FROM [oplan3].[dbo].[program] WHERE program_id = @oplan_program_id) as program_name,
                'Программа добавлена в расписание' as status;
            '''
            cursor.execute(query, (schedule_id, oplan_program_id, to_container, new_index))
            result = cursor.fetchall()
        return {'status': 'success', 'message': str(result)}
    except Exception as error:
        print(error)
        return {'status': 'error', 'message': str(error)}