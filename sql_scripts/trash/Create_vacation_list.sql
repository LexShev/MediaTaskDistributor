USE planner;
 
CREATE TABLE [vacation_schedule]
(	[vacation_id] INT PRIMARY KEY IDENTITY NOT NULL,
    [worker_id] INT NOT NULL,
    [worker] NVARCHAR(100) NOT NULL,
	[start_date] DATE,
	[end_date] DATE,
	[description] NVARCHAR(MAX)
);

INSERT INTO [planner].[dbo].[vacation_schedule]
([worker_id], [worker], [start_date], [end_date])
VALUES 
(0, 'Александр Кисляков', '2025-03-11', '2025-03-25'),
(1, 'Ольга Кузовкина', '2025-03-25', '2025-04-10'),
(2, 'Дмитрий Гатенян', NULL, NULL),
(3, 'Мария Сучкова', NULL, NULL),
(4, 'Андрей Антипин', NULL, NULL),
(5, 'Роман Рогачев', NULL, NULL),
(6, 'Анастасия Чебакова', NULL, NULL),
(7, 'Никита Кузаков', NULL, NULL),
(8, 'Олег Кашежев', NULL, NULL),
(9, 'Марфа Тарусина', NULL, NULL),
(10, 'Евгений Доманов', '2025-04-25', '2025-05-10');

