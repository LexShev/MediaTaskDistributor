USE planner;

CREATE TABLE task_list_backup
(
    program_id INT PRIMARY KEY NOT NULL,
    engineer_id INT,
    duration INT NOT NULL,
	sched_id INT,
	sched_date DATE,
	work_date DATE,
	ready_date DATE,
	task_status NVARCHAR(30) NOT NULL,
	file_path NVARCHAR(MAX),
);

-- Копируем данные
INSERT INTO [planner].[dbo].[task_list_backup]
SELECT * 
FROM [planner].[dbo].[task_list];