USE planner;
 
CREATE TABLE [vacation_schedule]
(	[vacation_id] INT PRIMARY KEY IDENTITY NOT NULL,
    [worker_id] INT NOT NULL,
    [worker] NVARCHAR(100) NOT NULL,
	[start_date] DATE,
	[end_date] DATE,
	[description] NVARCHAR(MAX)
);

INSERT INTO [{PLANNER_DB}].[dbo].[vacation_schedule]
([worker_id], [worker], [start_date], [end_date])
VALUES 
(0, '��������� ��������', '2025-03-11', '2025-03-25'),
(1, '����� ���������', '2025-03-25', '2025-04-10'),
(2, '������� �������', NULL, NULL),
(3, '����� �������', NULL, NULL),
(4, '������ �������', NULL, NULL),
(5, '����� �������', NULL, NULL),
(6, '��������� ��������', NULL, NULL),
(7, '������ �������', NULL, NULL),
(8, '���� �������', NULL, NULL),
(9, '����� ��������', NULL, NULL),
(10, '������� �������', '2025-04-25', '2025-05-10');

