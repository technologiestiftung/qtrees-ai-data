CREATE OR REPLACE FUNCTION public.rainfall (tree_id TEXT)
  RETURNS TABLE (
    date date, rainfall_in_mm real)
  LANGUAGE plpgsql
  AS $$
BEGIN
  RETURN query
  SELECT
    grouped.weekday AS "timestamp",
    grouped.daily_rainfall_sum_mm AS rainfall_in_mm
  FROM (
    SELECT
      public.radolan_tiles.geometry AS geom,
      date_trunc('day', qtrees.public.radolan.timestamp)::date AS weekday,
      sum(qtrees.public.radolan.rainfall_mm) AS daily_rainfall_sum_mm
    FROM
      qtrees.public.radolan 
      JOIN qtrees.public.radolan_tiles ON qtrees.public.radolan.tile_id=qtrees.public.radolan_tiles.id 
    GROUP BY
      geometry,
      weekday) AS grouped
WHERE
  weekday >= CURRENT_DATE at time zone 'UTC' - interval '13 days'
  AND ST_Contains(grouped.geom, (
      SELECT
        geometry FROM public.trees
      WHERE
        id = tree_id))
ORDER BY
  weekday DESC;
END;
$$;

CREATE OR REPLACE FUNCTION private.truncate_tables()
  RETURNS void AS
$$
DECLARE
    exec_str TEXT;
BEGIN
  SELECT INTO exec_str 'TRUNCATE TABLE '
       || string_agg(quote_ident(schemaname) || '.' || quote_ident(tablename), ', ')
       || ' CASCADE'
   FROM   pg_tables
   WHERE  (schemaname = 'public' OR schemaname = 'private')
   -- add exceptions here
   AND    tablename != 'spatial_ref_sys';

   RAISE NOTICE '%', exec_str;
   EXECUTE exec_str;
END
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION public.nowcast_input(_nowcast_date date, _type_id int)
  RETURNS TABLE (tree_id text, type_id int, nowcast_date date, shading_spring real, shading_summer real, shading_fall real, shading_winter real, 
				 tree_gattung text, tree_standalter real,  weather_rainfall_mm_14d_sum real, weather_temp_avg_c_14d_avg real, sensor_group_median real)
  LANGUAGE sql
  AS 
$body$
	SELECT trees.id as tree_id, _type_id as type_id, _nowcast_date as nowcast_date,
	shading.spring, shading.summer, shading.fall, shading.winter, trees.gattung_deutsch, trees.standalter, 
	(select rainfall_mm_14d_sum FROM private.weather_solaranywhere_14d_agg WHERE date = _nowcast_date),
	(select temp_avg_c_14d_avg FROM private.weather_solaranywhere_14d_agg WHERE date = _nowcast_date),
	(select median_value FROM private.sensor_measurements_agg WHERE (date(sensor_measurements_agg.timestamp) = _nowcast_date) AND sensor_measurements_agg.type_id = _type_id)
	FROM (SELECT * FROM public.trees WHERE trees.street_tree = True) AS trees LEFT JOIN public.shading ON shading.tree_id = trees.id
$body$;

-- all users (are derived from authenticator and) have access to rainfall
grant execute on function public.rainfall(text) to authenticator;