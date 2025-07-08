CREATE DATABASE oplan3;
CREATE DATABASE planner;
CREATE DATABASE service;

USE planner;

CREATE TABLE task_list
(
    program_id INT PRIMARY KEY NOT NULL,
    engineer_id INT,
    duration INT NOT NULL,
	sched_id INT,
	sched_date DATE,
	work_date DATE NOT NULL,
	ready_date DATE,
	task_status NVARCHAR(30) NOT NULL,
	file_path NVARCHAR(MAX),
);

CREATE TABLE [vacation_schedule]
(	[vacation_id] INT PRIMARY KEY IDENTITY NOT NULL,
    [worker_id] INT NOT NULL,
	[start_date] DATE,
	[end_date] DATE,
	[description] NVARCHAR(MAX)
);

INSERT INTO [planner].[dbo].[vacation_schedule]
(worker_id, start_date, end_date)
VALUES 
(0, '2025-03-10', '2025-03-20'),
(5, '2025-04-13', '2025-04-23');

CREATE TABLE worker_list
(
    worker_id INT NOT NULL,
	permission_group NVARCHAR(50) NOT NULL,
	fired BIT
);

INSERT INTO [planner].[dbo].[worker_list]
(worker_id, permission_group, fired)
VALUES 
(0, 'preparation_engineer', 0),
(1, 'preparation_engineer', 0),
(2, 'preparation_engineer', 0),
(3, 'preparation_engineer', 0),
(4, 'preparation_engineer', 1),
(5, 'preparation_engineer', 0),
(6, 'broadcast_engineer', 0),
(7, 'preparation_engineer', 0),
(8, 'preparation_engineer', 0),
(9, 'preparation_engineer', 0),
(10, 'preparation_engineer', 0),
(11, 'admin', 0);

CREATE TABLE permission_list
(
	[permission_group] NVARCHAR(50) NOT NULL,
	[home] BIT NOT NULL,
	[day] BIT NOT NULL,
	[on_air_report] BIT NOT NULL,
	[week] BIT NOT NULL,
	[list] BIT NOT NULL,
	[kpi_info] BIT NOT NULL,
	[work_calendar] BIT NOT NULL,
	[common_pool] BIT NOT NULL,
	[full_info_card] BIT NOT NULL,
	[otk] BIT NOT NULL,
	[advanced_search] BIT NOT NULL,
	[task_manager] BIT NOT NULL,
	[messenger] BIT NOT NULL,
	[desktop] BIT NOT NULL,
);

INSERT INTO [planner].[dbo].[permission_list]
([permission_group], [home], [day], [on_air_report], [week], [list], [kpi_info], [work_calendar], [common_pool], [full_info_card], [otk], [advanced_search], [task_manager], [messenger], [desktop])
VALUES 
('admin', 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1),
('preparation_engineer', 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1),
('broadcast_engineer', 1, 0, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1),
('otk_engineer', 1, 0, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1),
('editor', 1, 0, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1);


CREATE TABLE material_lock
(
    program_id INT PRIMARY KEY NOT NULL,
	lock_type NVARCHAR(30),
    worker_id INT NOT NULL,
	lock_time DATETIME NOT NULL,
);

CREATE TABLE history_list
(
    action_id INT PRIMARY KEY IDENTITY NOT NULL,
	program_id INT NOT NULL,
	CustomFieldID INT NOT NULL,
	action_description NVARCHAR(MAX),
	action_comment NVARCHAR(MAX),
    worker_id INT NOT NULL,
	time_of_change DATETIME NOT NULL,
	old_value NVARCHAR(MAX),
	new_value NVARCHAR(MAX)
);

CREATE TABLE [days_off]
(
	[day_off] DATE,
);

INSERT INTO [planner].[dbo].[days_off]
VALUES
('2025-01-01'),
('2025-01-02'),
('2025-01-03'),
('2025-01-04'),
('2025-01-05'),
('2025-01-06'),
('2025-01-07'),
('2025-01-08'),
('2025-01-11'),
('2025-01-12'),
('2025-01-18'),
('2025-01-19'),
('2025-01-25'),
('2025-01-26'),
('2025-02-01'),
('2025-02-02'),
('2025-02-08'),
('2025-02-09'),
('2025-02-15'),
('2025-02-16'),
('2025-02-22'),
('2025-02-23'),
('2025-02-24'),
('2025-03-01'),
('2025-03-02'),
('2025-03-08'),
('2025-03-09'),
('2025-03-10'),
('2025-03-15'),
('2025-03-16'),
('2025-03-22'),
('2025-03-23'),
('2025-03-29'),
('2025-03-30'),
('2025-04-05'),
('2025-04-06'),
('2025-04-12'),
('2025-04-13'),
('2025-04-19'),
('2025-04-20'),
('2025-04-26'),
('2025-04-27'),
('2025-05-01'),
('2025-05-03'),
('2025-05-04'),
('2025-05-09'),
('2025-05-10'),
('2025-05-11'),
('2025-05-17'),
('2025-05-18'),
('2025-05-24'),
('2025-05-25'),
('2025-05-31'),
('2025-06-01'),
('2025-06-07'),
('2025-06-08'),
('2025-06-12'),
('2025-06-14'),
('2025-06-15'),
('2025-06-21'),
('2025-06-22'),
('2025-06-28'),
('2025-06-29'),
('2025-07-05'),
('2025-07-06'),
('2025-07-12'),
('2025-07-13'),
('2025-07-19'),
('2025-07-20'),
('2025-07-26'),
('2025-07-27'),
('2025-08-02'),
('2025-08-03'),
('2025-08-09'),
('2025-08-10'),
('2025-08-16'),
('2025-08-17'),
('2025-08-23'),
('2025-08-24'),
('2025-08-30'),
('2025-08-31'),
('2025-09-06'),
('2025-09-07'),
('2025-09-13'),
('2025-09-14'),
('2025-09-20'),
('2025-09-21'),
('2025-09-27'),
('2025-09-28'),
('2025-10-04'),
('2025-10-05'),
('2025-10-11'),
('2025-10-12'),
('2025-10-18'),
('2025-10-19'),
('2025-10-25'),
('2025-10-26'),
('2025-11-01'),
('2025-11-02'),
('2025-11-04'),
('2025-11-08'),
('2025-11-09'),
('2025-11-15'),
('2025-11-16'),
('2025-11-22'),
('2025-11-23'),
('2025-11-29'),
('2025-11-30'),
('2025-12-06'),
('2025-12-07'),
('2025-12-13'),
('2025-12-14'),
('2025-12-20'),
('2025-12-21'),
('2025-12-27'),
('2025-12-28');

CREATE TABLE comments_history
(
	comment_id INT PRIMARY KEY IDENTITY NOT NULL,
	program_id INT NOT NULL,
	task_status NVARCHAR(30),
	worker_id INT NOT NULL,
	comment NVARCHAR(MAX),
    deadline DATE,
	time_of_change DATETIME NOT NULL,
);

CREATE TABLE banner_list
(
    program_id INT PRIMARY KEY NOT NULL,
	date_of_addition DATE NOT NULL,
	in_work BIT NOT NULL
);

CREATE TABLE filepath_history
(
	history_id INT PRIMARY KEY IDENTITY NOT NULL,
	program_id INT NOT NULL,
	file_path NVARCHAR(MAX) NOT NULL,
	engineer_id INT NOT NULL,
	duration INT,
	task_status NVARCHAR(30),
	time_of_change DATETIME NOT NULL,
);