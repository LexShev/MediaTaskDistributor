USE planner;
 
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