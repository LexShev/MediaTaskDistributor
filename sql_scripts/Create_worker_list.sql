USE planner;
 
CREATE TABLE worker_list
(
    worker_id INT NOT NULL,
    worker NVARCHAR(100) NOT NULL,
	vacation DATE,
	fired BIT
);

INSERT INTO [planner].[dbo].[vacation_schedule]
(worker_id, worker, holiday)
VALUES 
(0, '��������� ��������'),
(1,	'����� ���������'),
(2,	'������� �������'),
(3,	'����� �������'),
(4,	'������ �������'),
(5,	'����� �������'),
(6,	'��������� ��������'),
(7,	'������ �������'),
(8,	'���� �������'),
(9,	'����� ��������'),
(10, '������� �������');