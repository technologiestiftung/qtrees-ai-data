-- Change the id in the nowcast and forecast to cycle when it reaches the max value
-- Avoiding the need to delete the table and recreate it
ALTER SEQUENCE forecast_id_seq CYCLE;  
ALTER SEQUENCE nowcast_id_seq CYCLE;  