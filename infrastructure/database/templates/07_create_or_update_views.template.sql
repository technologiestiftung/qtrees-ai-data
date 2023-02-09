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

CREATE MATERIALIZED VIEW public.vector_tiles AS
SELECT
	trees.id AS trees_id,
	trees.standortnr AS trees_standortnr,
	trees.kennzeich AS trees_kennzeich,
	trees.namenr AS trees_namenr,
	trees.art_dtsch AS trees_art_dtsch,
	trees.art_bot AS trees_art_bot,
	trees.gattung_deutsch AS trees_gattung_deutsch,
	trees.gattung AS trees_gattung,
	trees.strname AS trees_strname,
	trees.hausnr AS trees_hausnr,
	trees.pflanzjahr AS trees_pflanzjahr,
	trees.standalter AS trees_standalter,
	trees.stammumfg AS trees_stammumfg,
	trees.baumhoehe AS trees_baumhoehe,
	trees.bezirk AS trees_bezirk,
	trees.eigentuemer AS trees_eigentuemer,
	trees.zusatz AS trees_zusatz,
	trees.kronedurch AS trees_kronedurch,
	trees.geometry AS trees_geometry,
	trees.lat AS trees_lat,
	trees.lng AS trees_lng,
	trees.created_at AS trees_created_at,
	trees.updated_at AS trees_updated_at,
	trees.street_tree AS trees_street_tree,
	trees.baumscheibe AS trees_baumscheibe,
	_nowcast.tree_id AS nowcast_tree_id,
	_nowcast.nowcast_type_30cm AS nowcast_type_30cm,
	_nowcast.nowcast_type_60cm AS nowcast_type_60cm,
	_nowcast.nowcast_type_90cm AS nowcast_type_90cm,
	_nowcast.nowcast_type_stamm AS nowcast_type_stamm,
	_nowcast.nowcast_timestamp_30cm AS nowcast_timestamp_30cm,
	_nowcast.nowcast_timestamp_60cm AS nowcast_timestamp_60cm,
	_nowcast.nowcast_timestamp_90cm AS nowcast_timestamp_90cm,
	_nowcast.nowcast_timestamp_stamm AS nowcast_timestamp_stamm,
	_nowcast.nowcast_values_30cm AS nowcast_values_30cm,
	_nowcast.nowcast_values_60cm AS nowcast_values_60cm,
	_nowcast.nowcast_values_90cm AS nowcast_values_90cm,
	_nowcast.nowcast_values_stamm AS nowcast_values_stamm,
	_nowcast.nowcast_created_at_30cm AS nowcast_created_at_30cm,
	_nowcast.nowcast_created_at_60cm AS nowcast_created_at_60cm,
	_nowcast.nowcast_created_at_90cm AS nowcast_created_at_90cm,
	_nowcast.nowcast_created_at_stamm AS nowcast_created_at_stamm,
	_nowcast.nowcast_model_id_30cm AS nowcast_model_id_30cm,
	_nowcast.nowcast_model_id_60cm AS nowcast_model_id_60cm,
	_nowcast.nowcast_model_id_90cm AS nowcast_model_id_90cm,
	_nowcast.nowcast_model_id_stamm AS nowcast_model_id_4
FROM
	public.trees
	LEFT JOIN (
		SELECT
			nowcast_tree_id AS tree_id,
			ARRAY_AGG(DISTINCT distinct_nowcast.forcast_type ORDER BY distinct_nowcast.forcast_type) AS nowcast_types_array,
			(ARRAY_AGG(sensor_types_id)) [1] nowcast_type_30cm,
			(ARRAY_AGG(sensor_types_id)) [2] nowcast_type_60cm,
			(ARRAY_AGG(sensor_types_id)) [3] nowcast_type_90cm,
			(ARRAY_AGG(sensor_types_id)) [4] nowcast_type_stamm,
			(ARRAY_AGG(distinct_nowcast.nowcast_value)) [1] nowcast_values_30cm,
			(ARRAY_AGG(distinct_nowcast.nowcast_value)) [2] nowcast_values_60cm,
			(ARRAY_AGG(distinct_nowcast.nowcast_value)) [3] nowcast_values_90cm,
			(ARRAY_AGG(distinct_nowcast.nowcast_value)) [4] nowcast_values_stamm,
			(ARRAY_AGG(nowcast_model_id)) [1] nowcast_model_id_30cm,
			(ARRAY_AGG(nowcast_model_id)) [2] nowcast_model_id_60cm,
			(ARRAY_AGG(nowcast_model_id)) [3] nowcast_model_id_90cm,
			(ARRAY_AGG(nowcast_model_id)) [4] nowcast_model_id_stamm,
			(ARRAY_AGG(nowcast_created_at)) [1] nowcast_created_at_30cm,
			(ARRAY_AGG(nowcast_created_at)) [2] nowcast_created_at_60cm,
			(ARRAY_AGG(nowcast_created_at)) [3] nowcast_created_at_90cm,
			(ARRAY_AGG(nowcast_created_at)) [4] nowcast_created_at_stamm,
			(ARRAY_AGG(nowcast_timestamp)) [1] nowcast_timestamp_30cm,
			(ARRAY_AGG(nowcast_timestamp)) [2] nowcast_timestamp_60cm,
			(ARRAY_AGG(nowcast_timestamp)) [3] nowcast_timestamp_90cm,
			(ARRAY_AGG(nowcast_timestamp)) [4] nowcast_timestamp_stamm
		FROM ( SELECT DISTINCT ON (n.tree_id, f.name)
				n.id AS nowcast_id,
				n.timestamp AS nowcast_timestamp,
				n.tree_id AS nowcast_tree_id,
				n.value AS nowcast_value,
				n.created_at AS nowcast_created_at,
				n.model_id AS nowcast_model_id,
				f.name AS forcast_type,
				f.id AS sensor_types_id
			FROM
				public.nowcast n
				JOIN public.sensor_types f ON n.type_id = f.id
			ORDER BY
				n.tree_id,
				f.name,
				n.timestamp DESC) distinct_nowcast
		GROUP BY
			nowcast_tree_id) AS _nowcast ON trees.id = _nowcast.tree_id;

CREATE OR REPLACE VIEW private.test_data AS
SELECT trees.id, trees.gattung_deutsch, trees.standalter,
		shading.winter, shading.spring, shading.summer, shading.fall,
		(SELECT weather.rainfall_mm  FROM public.weather WHERE timestamp = (SELECT current_date - INTEGER '1')) as rainfall_mm,
		(SELECT weather.temp_avg_c  FROM public.weather WHERE timestamp = (SELECT current_date - INTEGER '1')) as temp_mean,
		(SELECT weather.temp_max_c FROM public.weather WHERE timestamp = (SELECT current_date - INTEGER '1')) as temp_max
FROM public.trees
LEFT JOIN public.shading ON public.shading.tree_id = public.trees.id;

CREATE MATERIALIZED VIEW public.watering AS
SELECT tree_id, sum(amount_liters), "date"
FROM ((
  SELECT tree_id, amount_liters, "date" FROM private.watering_gdk
  UNION ALL
  SELECT tree_id, amount_liters, "date" FROM private.watering_sga
)) w
WHERE "date" >= cast(now() as date) - interval '2 months'
GROUP BY tree_id, "date";

-- all users (are derived from authenticator and) have access to rainfall
grant select on public.rainfall to authenticator;
grant select on public.rainfall to web_anon;

grant select on public.vector_tiles to authenticator;
grant select on public.vector_tiles to web_anon;

grant select on public.watering to authenticator;
grant select on public.watering to web_anon;
