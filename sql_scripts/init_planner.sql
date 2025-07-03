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
    [worker] NVARCHAR(100) NOT NULL,
	[start_date] DATE,
	[end_date] DATE,
	[description] NVARCHAR(MAX)
);

INSERT INTO [planner].[dbo].[vacation_schedule]
(worker_id, worker, holiday)
VALUES 
(0, 'Александр Кисляков'),
(1,	'Ольга Кузовкина'),
(2,	'Дмитрий Гатенян'),
(3,	'Мария Сучкова'),
(4,	'Андрей Антипин'),
(5,	'Роман Рогачев'),
(6,	'Анастасия Чебакова'),
(7,	'Никита Кузаков'),
(8,	'Олег Кашежев'),
(9,	'Марфа Тарусина'),
(10, 'Евгений Доманов');

CREATE TABLE worker_list
(
    worker_id INT NOT NULL,
    worker NVARCHAR(100) NOT NULL,
	permission_group NVARCHAR(50) NOT NULL,
	fired BIT
);

INSERT INTO [planner].[dbo].[worker_list]
(worker_id, worker, permission_group)
VALUES 
(0, 'Александр Кисляков', 'preparation_engineer'),
(1, 'Ольга Кузовкина', 'preparation_engineer'),
(2, 'Дмитрий Гатенян', 'preparation_engineer'),
(3, 'Мария Сучкова', 'preparation_engineer'),
(4, 'Андрей Антипин', 'preparation_engineer'),
(5, 'Роман Рогачев', 'preparation_engineer'),
(6, 'Анастасия Чебакова', 'broadcast_engineer'),
(7, 'Никита Кузаков', 'preparation_engineer'),
(8, 'Олег Кашежев', 'preparation_engineer'),
(9, 'Марфа Тарусина', 'preparation_engineer'),
(10, 'Евгений Доманов', 'preparation_engineer'),
(11, 'Евгений Доманов', 'admin');

INSERT INTO [planner].[dbo].[vacation_schedule]
(worker_id, worker, permission_group)
VALUES 
(0, 'Александр Кисляков', 0),
(1,	'Ольга Кузовкина', 0),
(2,	'Дмитрий Гатенян', 0),
(3,	'Мария Сучкова', 0),
(4,	'Андрей Антипин', 0),
(5,	'Роман Рогачев', 0),
(6,	'Анастасия Чебакова', 0),
(7,	'Никита Кузаков', 0),
(8,	'Олег Кашежев', 0),
(9,	'Марфа Тарусина', 0),
(10, 'Евгений Доманов', 0);

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