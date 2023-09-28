CREATE TABLE IF NOT EXISTS public.db_change_management (
reason varchar (100), 
date varchar(50)
);

INSERT INTO public.db_change_management
VALUES ('we are testing db_change_management', '27 Sep');
