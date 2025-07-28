USE planner;
 
CREATE TABLE worker_list
(
    worker_id INT NOT NULL,
    worker NVARCHAR(100) NOT NULL,
	permission_group NVARCHAR(50) NOT NULL,
	fired BIT
);

INSERT INTO [{PLANNER_DB}].[dbo].[worker_list]
(worker_id, worker, permission_group)
VALUES 
(0, '��������� ��������', 'preparation_engineer'),
(1, '����� ���������', 'preparation_engineer'),
(2, '������� �������', 'preparation_engineer'),
(3, '����� �������', 'preparation_engineer'),
(4, '������ �������', 'preparation_engineer'),
(5, '����� �������', 'preparation_engineer'),
(6, '��������� ��������', 'broadcast_engineer'),
(7, '������ �������', 'preparation_engineer'),
(8, '���� �������', 'preparation_engineer'),
(9, '����� ��������', 'preparation_engineer'),
(10, '������� �������', 'preparation_engineer'),
(11, '������� �������', 'admin');