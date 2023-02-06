-- views
CREATE MATERIALIZED VIEW public.weather_14d_agg AS
select timestamp, 
		sum(rainfall_mm) OVER(ORDER BY timestamp ROWS BETWEEN 13 PRECEDING AND CURRENT ROW ) as rainfall_mm_14d_sum, 
		avg(temp_avg_c) OVER(ORDER BY timestamp ROWS BETWEEN 13 PRECEDING AND CURRENT ROW ) as temp_avg_c_14d_avg,
		avg(wind_mean_ms) OVER(ORDER BY timestamp ROWS BETWEEN 13 PRECEDING AND CURRENT ROW ) as wind_avg_ms_14d_avg,
		avg(temp_max_c) OVER(ORDER BY timestamp ROWS BETWEEN 13 PRECEDING AND CURRENT ROW ) as temp_max_c_14d_avg,
		avg(wind_max_ms) OVER(ORDER BY timestamp ROWS BETWEEN 13 PRECEDING AND CURRENT ROW ) as wind_max_ms_14d_avg
from public.weather
where stations_id = 433;

CREATE MATERIALIZED VIEW public.tree_radolan_tile AS
select trees.id as tree_id, tiles.id as tile_id
from public.trees as trees
join public.radolan_tiles as tiles
ON ST_Contains(tiles.geometry, trees.geometry);

CREATE MATERIALIZED VIEW public.radolan_14d_agg AS
SELECT radolan.timestamp, radolan.tile_id,
SUM(radolan.rainfall_mm) OVER (partition by radolan.tile_id ORDER BY radolan.timestamp ROWS BETWEEN 14*24-1 PRECEDING AND CURRENT ROW) AS rainfall_mm_14d_sum
FROM public.radolan;

CREATE MATERIALIZED VIEW public.rainfall AS
SELECT public.tree_radolan_tile.tree_id, tile_rainfall.rainfall_mm_14d_sum as rainfall_in_mm
FROM public.tree_radolan_tile 
JOIN 
	(SELECT DISTINCT ON (tile_id)
	tile_id, rainfall_mm_14d_sum
	FROM public.radolan_14d_agg
	ORDER BY tile_id, timestamp DESC) as tile_rainfall
ON public.tree_radolan_tile.tile_id = tile_rainfall.tile_id;

CREATE OR REPLACE VIEW private.training_data AS
SELECT sensor_measurements.tree_id, sensor_measurements.sensor_id, sensor_measurements.timestamp, sensor_measurements.value,
		shading.winter, shading.spring, shading.summer, shading.fall,
		trees.gattung_deutsch, trees.standalter,
		weather_14d_agg.temp_avg_c_14d_avg, weather_14d_agg.wind_avg_ms_14d_avg, weather_14d_agg.temp_max_c_14d_avg, weather_14d_agg.wind_max_ms_14d_avg 
FROM private.sensor_measurements
LEFT JOIN public.shading ON public.shading.tree_id = sensor_measurements.tree_id
LEFT JOIN public.trees ON trees.id = sensor_measurements.tree_id
LEFT JOIN public.weather_14d_agg ON sensor_measurements.timestamp = weather_14d_agg.timestamp
LEFT JOIN public.radolan_14d_agg ON sensor_measurements.timestamp = radolan_14d_agg.timestamp
ORDER BY timestamp DESC;

CREATE OR REPLACE VIEW private.test_data AS
SELECT trees.id, trees.gattung_deutsch, trees.standalter,
		shading.winter, shading.spring, shading.summer, shading.fall,
		(SELECT weather.rainfall_mm  FROM public.weather WHERE timestamp = (SELECT current_date - INTEGER '1')) as rainfall_mm,
		(SELECT weather.temp_avg_c  FROM public.weather WHERE timestamp = (SELECT current_date - INTEGER '1')) as temp_mean,
		(SELECT weather.temp_max_c FROM public.weather WHERE timestamp = (SELECT current_date - INTEGER '1')) as temp_max
FROM public.trees
LEFT JOIN public.shading ON public.shading.tree_id = public.trees.id;

-- all users (are derived from authenticator and) have access to rainfall
grant select on public.rainfall to authenticator;
grant select on public.rainfall to web_anon;