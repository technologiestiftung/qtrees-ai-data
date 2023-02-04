CREATE OR REPLACE FUNCTION public.rainfall (tree_id TEXT)
  RETURNS TABLE (
    date date, rainfall_in_mm float8)
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

-- all users (are derived from authenticator and) have access to rainfall
grant execute on function public.rainfall(text) to authenticator;