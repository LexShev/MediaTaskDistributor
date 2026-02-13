DECLARE @start_date DATE
    SET @start_date = '2025-09-01'
DECLARE @end_date DATE
    SET @end_date = '2026-02-12'

-- Общая статистика по задачам
SELECT 
    Task.worker_id,
    Us.username,
    Us.first_name,
    Us.last_name,
    SUM(CASE WHEN Task.[noCENZ] = 0 THEN 1 ELSE 0 END) as CENZ,
    SUM(CASE WHEN Task.[noCENZ] = 1 THEN 1 ELSE 0 END) as noCENZ,
    SUM(CASE WHEN Task.[noCENZ] NOT IN (0, 1) OR Task.[noCENZ] IS NULL THEN 1 ELSE 0 END) as in_work,
    CAST(SUM(CASE WHEN Task.[noCENZ] = 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS DECIMAL(5,2)) as CENZ_percent,
    CAST(SUM(CASE WHEN Task.[noCENZ] = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS DECIMAL(5,2)) as noCENZ_percent,
    COUNT(*) as TOTAL
FROM [planner].[dbo].[task_list] AS Task
LEFT JOIN [planner].[dbo].[auth_user] AS Us
    ON Task.worker_id = Us.id
WHERE Task.[ready_date] IS NOT NULL
    AND Task.ready_date BETWEEN @start_date AND DATEADD(DAY, 1, @end_date)
    AND Task.worker_id IN (3, 4, 5, 7, 8, 9, 10, 11, 12, 13)
GROUP BY Task.worker_id, Us.username, Us.first_name, Us.last_name
ORDER BY Task.worker_id

-- Запрошено фиксов
SELECT 
    u.id as worker_id,
    u.username,
    u.first_name,
    u.last_name,
    COUNT(h.worker_id) as fix_tasks_count
FROM [planner].[dbo].[auth_user] u
LEFT JOIN [planner].[dbo].[history_status_list] h 
    ON u.id = h.worker_id 
    AND h.[new_status] = 'fix'
    AND h.time_of_change BETWEEN @start_date AND DATEADD(DAY, 1, @end_date)
WHERE u.id IN (3, 4, 5, 7, 8, 9, 10, 11, 12, 13)
GROUP BY u.id, u.username, u.first_name, u.last_name
ORDER BY worker_id

-- Оставлено уникальных комментариев
SELECT 
    u.id as worker_id,
    u.username,
    u.first_name,
    u.last_name,
    COUNT(ch.comment_id) as comments_count
FROM [planner].[dbo].[auth_user] u
LEFT JOIN [planner].[dbo].[comments_history] ch
    ON u.id = ch.worker_id 
    AND ch.time_of_change BETWEEN @start_date AND DATEADD(DAY, 1, @end_date)
    AND ch.[comment] NOT LIKE '%CENZ не требуется%'
    AND ch.[comment] IS NOT NULL
    AND ch.[comment] != ''
WHERE u.id IN (3, 4, 5, 7, 8, 9, 10, 11, 12, 13)
GROUP BY u.id, u.username, u.first_name, u.last_name
ORDER BY u.id

-- Расшивровка активности по дням
SELECT 
    worker_id,
    username,
    first_name,
    last_name,
    activity_date,
    first_activity,
    last_activity,
    CONCAT(
        RIGHT('0' + CAST(DATEDIFF(MINUTE, first_activity, last_activity) / 60 AS VARCHAR), 2),
        ':',
        RIGHT('0' + CAST(DATEDIFF(MINUTE, first_activity, last_activity) % 60 AS VARCHAR), 2)
    ) as work_duration
FROM (
    SELECT 
        worker_id,
        CONVERT(DATE, time_of_change) as activity_date,
        MIN(time_of_change) as first_activity,
        MAX(time_of_change) as last_activity
    FROM (
        -- Активности из history_status_list
        SELECT worker_id, time_of_change
        FROM [planner].[dbo].[history_status_list]
        WHERE worker_id IN (3, 4, 5, 7, 8, 9, 10, 11, 12, 13)
            AND time_of_change BETWEEN @start_date AND DATEADD(DAY, 1, @end_date)
        
        UNION ALL
        
        -- Активности из history_list
        SELECT worker_id, time_of_change
        FROM [planner].[dbo].[history_list]
        WHERE worker_id IN (3, 4, 5, 7, 8, 9, 10, 11, 12, 13)
            AND time_of_change BETWEEN @start_date AND DATEADD(DAY, 1, @end_date)
    ) as combined_activities
    GROUP BY worker_id, CONVERT(DATE, time_of_change)
) as daily_stats
LEFT JOIN [planner].[dbo].[auth_user] u ON daily_stats.worker_id = u.id
ORDER BY activity_date ASC, worker_id

-- Сводка по количеству отработанных дней
SELECT 
    worker_id,
    u.username,
    u.first_name,
    u.last_name,
    COUNT(DISTINCT activity_date) as work_days,
    CONCAT(
        RIGHT('0' + CAST(AVG(DATEDIFF(MINUTE, first_activity, last_activity)) / 60 AS VARCHAR), 2),
        ':',
        RIGHT('0' + CAST(AVG(DATEDIFF(MINUTE, first_activity, last_activity)) % 60 AS VARCHAR), 2)
    ) as avg_work_duration
FROM (
    SELECT 
        worker_id,
        CONVERT(DATE, time_of_change) as activity_date,
        MIN(time_of_change) as first_activity,
        MAX(time_of_change) as last_activity
    FROM (
        -- Активности из history_status_list
        SELECT worker_id, time_of_change
        FROM [planner].[dbo].[history_status_list]
        WHERE worker_id IN (3, 4, 5, 7, 8, 9, 10, 11, 12, 13)
            AND time_of_change BETWEEN @start_date AND DATEADD(DAY, 1, @end_date)
        
        UNION ALL
        
        -- Активности из history_list
        SELECT worker_id, time_of_change
        FROM [planner].[dbo].[history_list]
        WHERE worker_id IN (3, 4, 5, 7, 8, 9, 10, 11, 12, 13)
            AND time_of_change BETWEEN @start_date AND DATEADD(DAY, 1, @end_date)
    ) as combined_activities
    GROUP BY worker_id, CONVERT(DATE, time_of_change)
) as daily_stats
LEFT JOIN [planner].[dbo].[auth_user] u ON daily_stats.worker_id = u.id
GROUP BY worker_id, u.username, u.first_name, u.last_name
ORDER BY worker_id


-- '2025-11-20'

;WITH DateRange AS (
    SELECT @start_date AS report_date
    UNION ALL
    SELECT DATEADD(DAY, 1, report_date)
    FROM DateRange
    WHERE report_date < @end_date
),
AllUsers AS (
    SELECT id, username, first_name, last_name
    FROM auth_user
    WHERE id IN (3, 4, 5, 7, 8, 9, 10, 11, 12, 13)
)
SELECT 
    au.id AS worker_id,
    au.username,
    au.first_name,
    au.last_name,
    dr.report_date AS activity_date,
    CASE 
        WHEN dwt.first_request IS NOT NULL THEN FORMAT(DATEADD(HOUR, 3, dwt.first_request), 'HH:mm:ss')
        ELSE '--:--:--'
    END AS first_activity,
    CASE 
        WHEN dwt.last_request IS NOT NULL THEN FORMAT(DATEADD(HOUR, 3, dwt.last_request), 'HH:mm:ss')
        ELSE '--:--:--'
    END AS last_activity,
    CASE 
        WHEN dwt.first_request IS NOT NULL AND dwt.last_request IS NOT NULL THEN
            CONCAT(
                RIGHT('0' + CAST(DATEDIFF(MINUTE, dwt.first_request, dwt.last_request) / 60 AS VARCHAR(2)), 2),
                ':',
                RIGHT('0' + CAST(DATEDIFF(MINUTE, dwt.first_request, dwt.last_request) % 60 AS VARCHAR(2)), 2)
            )
        ELSE '00:00'
    END AS work_duration,
    COALESCE(dwt.total_requests, 0) AS total_requests
FROM AllUsers au
CROSS JOIN DateRange dr
LEFT JOIN workers_dailyworktime dwt ON au.id = dwt.user_id AND dr.report_date = dwt.date
ORDER BY au.username, dr.report_date;


DECLARE @start_date DATE
SET @start_date = '2025-09-01'

DECLARE @end_date DATE
SET @end_date = '2026-02-12'

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



DECLARE @start_date DATE
SET @start_date = '2025-09-01'

DECLARE @end_date DATE
SET @end_date = '2026-02-12'

-- !Создаем 7-дневные интервалы
DECLARE @week_ranges TABLE (week_start DATE, week_end DATE, week_number INT)
DECLARE @current_start DATE = @start_date
DECLARE @week_num INT = 36

WHILE @current_start <= @end_date
BEGIN
    INSERT INTO @week_ranges 
    VALUES (
        @current_start, 
        DATEADD(day, 6, @current_start),
        @week_num
    )
    SET @current_start = DATEADD(day, 7, @current_start)
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
DECLARE @current_start DATE = @start_date

WHILE @current_start <= @end_date
BEGIN
    -- Начало месяца - первый день текущего месяца
    DECLARE @month_start DATE = DATEFROMPARTS(YEAR(@current_start), MONTH(@current_start), 1)
    -- Конец месяца - последний день текущего месяца
    DECLARE @month_end DATE = EOMONTH(@current_start)
    
    INSERT INTO @month_ranges 
    VALUES (
        @month_start,
        @month_end,
        FORMAT(@month_start, 'MMM yyyy', 'ru-RU')  -- Название месяца на русском
    )
    
    -- Переходим к следующему месяцу
    SET @current_start = DATEADD(month, 1, @month_start)
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