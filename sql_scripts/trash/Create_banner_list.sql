USE planner;
 
CREATE TABLE poster_list
(
    program_id INT PRIMARY KEY NOT NULL,
	date_of_addition DATE NOT NULL,
	in_work BIT NOT NULL
);