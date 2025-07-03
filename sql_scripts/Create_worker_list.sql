USE planner;
 
CREATE TABLE worker_list
(
    worker_id INT NOT NULL,
    worker NVARCHAR(100) NOT NULL,
	permission_group NVARCHAR(50) NOT NULL,
	fired BIT
);

INSERT INTO [planner].[dbo].[vacation_schedule]
(worker_id, worker, permission_group)
VALUES 
(0, '��������� ��������', 0),
(1,	'����� ���������', 0),
(2,	'������� �������', 0),
(3,	'����� �������', 0),
(4,	'������ �������', 0),
(5,	'����� �������', 0),
(6,	'��������� ��������', 0),
(7,	'������ �������', 0),
(8,	'���� �������', 0),
(9,	'����� ��������', 0),
(10, '������� �������', 0);