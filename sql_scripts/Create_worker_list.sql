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