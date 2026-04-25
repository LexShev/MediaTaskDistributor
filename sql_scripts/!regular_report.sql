use planner;

DECLARE @start_date DATE
SET @start_date = '2025-09-01'

DECLARE @end_date DATE
SET @end_date = '2026-04-30'

-- !Отчёт по дням
DECLARE @date_range TABLE (calendar_date DATE)
DECLARE @current_date DATE = @start_date
WHILE @current_date <= @end_date
BEGIN
    INSERT INTO @date_range VALUES (@current_date)
    SET @current_date = DATEADD(day, 1, @current_date)
END

-- Затем LEFT JOIN с данными
SELECT
    dr.calendar_date AS ready_date,
    Users.username,
    Users.first_name,
    Users.last_name,

    ISNULL(
        -- Формат ЧЧ:ММ:СС с ведущими нулями
        RIGHT('00' + CONVERT(VARCHAR(10), SUM(Task.duration) / 25 / 3600), 2) + ':' +
        RIGHT('00' + CONVERT(VARCHAR(2), (SUM(Task.duration) / 25 % 3600) / 60), 2) + ':' +
        RIGHT('00' + CONVERT(VARCHAR(2), SUM(Task.duration) / 25 % 60), 2),
        '--:--:--'
    ) AS hh_mm_ss

FROM @date_range dr
CROSS JOIN (
    SELECT DISTINCT id, username, first_name, last_name
    FROM [planner].[dbo].[auth_user]
    WHERE id IN (3, 4, 5, 7, 8, 9, 10, 11, 12, 13)
) Users
LEFT JOIN [planner].[dbo].[task_list] AS Task
    ON Task.worker_id = Users.id
    AND Task.[ready_date] = dr.calendar_date
    AND Task.[ready_date] BETWEEN @start_date AND @end_date
    AND Task.[task_status] IN ('ready', 'otk', 'final')

GROUP BY Users.id, Users.username, Users.first_name, Users.last_name, dr.calendar_date
ORDER BY dr.calendar_date, Users.username





-- !Создаем 7-дневные интервалы
DECLARE @week_ranges TABLE (week_start DATE, week_end DATE, week_number INT)
DECLARE @current_week_start DATE = @start_date
DECLARE @week_num INT = 36

WHILE @current_week_start <= @end_date
BEGIN
    INSERT INTO @week_ranges
    VALUES (
        @current_week_start,
        DATEADD(day, 6, @current_week_start),
        @week_num
    )
    SET @current_week_start = DATEADD(day, 7, @current_week_start)
    SET @week_num = @week_num + 1
END

-- Группировка по неделям
SELECT
    'Неделя ' + CAST(wr.week_number AS VARCHAR(10)) AS week_label,
    wr.week_start,
    wr.week_end,
    Users.username,
    Users.first_name,
    Users.last_name,

    ISNULL(
        RIGHT('00' + CONVERT(VARCHAR(10), SUM(Task.duration) / 25 / 3600), 2) + ':' +
        RIGHT('00' + CONVERT(VARCHAR(2), (SUM(Task.duration) / 25 % 3600) / 60), 2) + ':' +
        RIGHT('00' + CONVERT(VARCHAR(2), SUM(Task.duration) / 25 % 60), 2),
        '--:--:--'
    ) AS hh_mm_ss

FROM @week_ranges wr
CROSS JOIN (
    SELECT DISTINCT id, username, first_name, last_name
    FROM [planner].[dbo].[auth_user]
    WHERE id IN (3, 4, 5, 7, 8, 9, 10, 11, 12, 13)
) Users
LEFT JOIN [planner].[dbo].[task_list] AS Task
    ON Task.worker_id = Users.id
    AND Task.[ready_date] BETWEEN wr.week_start AND wr.week_end
    AND Task.[task_status] IN ('ready', 'otk', 'final')

GROUP BY Users.id, Users.username, Users.first_name, Users.last_name,
         wr.week_number, wr.week_start, wr.week_end
ORDER BY wr.week_number, Users.username





-- !Создаем месячные интервалы
DECLARE @month_ranges TABLE (month_start DATE, month_end DATE, month_year VARCHAR(20))
DECLARE @current_month_start DATE = @start_date

WHILE @current_month_start <= @end_date
BEGIN
    -- Начало месяца - первый день текущего месяца
    DECLARE @month_start DATE = DATEFROMPARTS(YEAR(@current_month_start), MONTH(@current_month_start), 1)
    -- Конец месяца - последний день текущего месяца
    DECLARE @month_end DATE = EOMONTH(@current_month_start)

    INSERT INTO @month_ranges
    VALUES (
        @month_start,
        @month_end,
        FORMAT(@month_start, 'MMM yyyy', 'ru-RU')  -- Название месяца на русском
    )

    -- Переходим к следующему месяцу
    SET @current_month_start = DATEADD(month, 1, @month_start)
END

-- Группировка по месяцам
SELECT
    wr.month_year AS month_label,
    wr.month_start,
    wr.month_end,
    Users.username,
    Users.first_name,
    Users.last_name,

    ISNULL(
        RIGHT('00' + CONVERT(VARCHAR(10), SUM(Task.duration) / 25 / 3600), 2) + ':' +
        RIGHT('00' + CONVERT(VARCHAR(2), (SUM(Task.duration) / 25 % 3600) / 60), 2) + ':' +
        RIGHT('00' + CONVERT(VARCHAR(2), SUM(Task.duration) / 25 % 60), 2),
        '--:--:--'
    ) AS hh_mm_ss

FROM @month_ranges wr
CROSS JOIN (
    SELECT DISTINCT id, username, first_name, last_name
    FROM [planner].[dbo].[auth_user]
    WHERE id IN (3, 4, 5, 7, 8, 9, 10, 11, 12, 13)
) Users
LEFT JOIN [planner].[dbo].[task_list] AS Task
    ON Task.worker_id = Users.id
    AND Task.[ready_date] BETWEEN wr.month_start AND wr.month_end
    AND Task.[task_status] IN ('ready', 'otk', 'final')

GROUP BY Users.id, Users.username, Users.first_name, Users.last_name,
         wr.month_start, wr.month_end, wr.month_year
ORDER BY wr.month_start, Users.username