-- views
CREATE MATERIALIZED VIEW public.weather_14d_agg AS
select date,
		sum(rainfall_mm) OVER(ORDER BY date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW ) as rainfall_mm_14d_sum,
		avg(temp_avg_c) OVER(ORDER BY date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW ) as temp_avg_c_14d_avg,
		avg(wind_avg_ms) OVER(ORDER BY date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW ) as wind_avg_ms_14d_avg,
		avg(temp_max_c) OVER(ORDER BY date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW ) as temp_max_c_14d_avg,
		avg(wind_max_ms) OVER(ORDER BY date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW ) as wind_max_ms_14d_avg
from public.weather
where stations_id = 433;

CREATE MATERIALIZED VIEW private.weather_solaranywhere_14d_agg AS
select date,
		sum(rainfall_mm) OVER(ORDER BY date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW ) as rainfall_mm_14d_sum,
		avg(temp_avg_c) OVER(ORDER BY date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW ) as temp_avg_c_14d_avg,
		avg(wind_avg_ms) OVER(ORDER BY date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW ) as wind_avg_ms_14d_avg,
		avg(temp_max_c) OVER(ORDER BY date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW ) as temp_max_c_14d_avg,
		avg(wind_max_ms) OVER(ORDER BY date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW ) as wind_max_ms_14d_avg
from private.weather_tile_measurement
where tile_id = 2;

CREATE MATERIALIZED VIEW public.tree_radolan_tile AS
select trees.id as tree_id, tiles.id as tile_id
from public.trees as trees
join public.radolan_tiles as tiles
ON ST_Contains(tiles.geometry, trees.geometry);

CREATE MATERIALIZED VIEW public.radolan_14d_agg AS
SELECT radolan.date, radolan.tile_id,
SUM(radolan.rainfall_mm) OVER (partition by radolan.tile_id ORDER BY radolan.date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW) AS rainfall_mm_14d_sum
FROM public.radolan;

CREATE MATERIALIZED VIEW public.rainfall AS
SELECT public.tree_radolan_tile.tree_id, tile_rainfall.rainfall_mm_14d_sum as rainfall_in_mm
FROM public.tree_radolan_tile
JOIN
	(SELECT DISTINCT ON (tile_id)
	tile_id, rainfall_mm_14d_sum
	FROM public.radolan_14d_agg
	ORDER BY tile_id, date DESC) as tile_rainfall
ON public.tree_radolan_tile.tile_id = tile_rainfall.tile_id;

CREATE MATERIALIZED VIEW private.sensor_measurements_agg AS
SELECT 
    type_id, 
    "timestamp", 
    AVG(CAST(value AS double precision)) AS mean_value,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY CAST(value AS double precision)) AS median_value
FROM 
    private.sensor_measurements 
GROUP BY 
    type_id, 
    "timestamp";

CREATE OR REPLACE VIEW private.nowcast_training_data AS
SELECT sensor_measurements.tree_id, sensor_measurements.type_id, sensor_measurements.timestamp as nowcast_date, 
		shading.winter as shading_winter, shading.spring as shading_spring, shading.summer as shading_summer, shading.fall as shading_fall,
		trees.gattung_deutsch as tree_gattung, trees.standalter as tree_standalter,
		weather_solaranywhere_14d_agg.rainfall_mm_14d_sum as weather_rainfall_mm_14d_sum, 
		weather_solaranywhere_14d_agg.temp_avg_c_14d_avg as weather_temp_avg_c_14d_avg,
		sensor_measurements_agg.median_value as sensor_group_median,
		sensor_measurements.value as target
FROM private.sensor_measurements
LEFT JOIN public.shading ON public.shading.tree_id = sensor_measurements.tree_id
LEFT JOIN public.trees ON trees.id = sensor_measurements.tree_id
LEFT JOIN private.weather_solaranywhere_14d_agg ON date(sensor_measurements.timestamp) = weather_solaranywhere_14d_agg.date
LEFT JOIN private.sensor_measurements_agg ON (date(sensor_measurements.timestamp) = date(sensor_measurements_agg.timestamp) AND sensor_measurements.type_id = sensor_measurements_agg.type_id)
ORDER BY tree_id, nowcast_date DESC;

CREATE OR REPLACE VIEW private.forecast_training_data AS
SELECT sensor_measurements.tree_id, sensor_measurements.type_id, sensor_measurements.timestamp as nowcast_date, 
		shading.winter as shading_winter, shading.spring as shading_spring, shading.summer as shading_summer, shading.fall as shading_fall,
		trees.gattung_deutsch as tree_gattung, trees.standalter as tree_standalter,
		weather_solaranywhere_14d_agg.rainfall_mm_14d_sum as weather_rainfall_mm_14d_sum, 
		weather_solaranywhere_14d_agg.temp_avg_c_14d_avg as weather_temp_avg_c_14d_avg,
		sensor_measurements_agg.median_value as sensor_group_median,
		current_weather.temp_max_c, current_weather.rainfall_mm,
		sensor_measurements.value as target
FROM private.sensor_measurements
LEFT JOIN public.shading ON public.shading.tree_id = sensor_measurements.tree_id
LEFT JOIN public.trees ON trees.id = sensor_measurements.tree_id
LEFT JOIN private.weather_solaranywhere_14d_agg ON date(sensor_measurements.timestamp) = weather_solaranywhere_14d_agg.date
LEFT JOIN private.sensor_measurements_agg ON (date(sensor_measurements.timestamp) = date(sensor_measurements_agg.timestamp) AND sensor_measurements.type_id = sensor_measurements_agg.type_id)
LEFT JOIN (SELECT DISTINCT ON (date) date, temp_max_c, rainfall_mm FROM private.weather_tile_forecast ORDER BY date, created_at DESC) AS current_weather ON date(sensor_measurements.timestamp) = current_weather.date
ORDER BY tree_id, nowcast_date DESC;

CREATE OR REPLACE VIEW private.forecast_training_data_dev AS
SELECT sensor_measurements.tree_id, sensor_measurements.type_id, sensor_measurements.timestamp as nowcast_date, 
		shading.winter as shading_winter, shading.spring as shading_spring, shading.summer as shading_summer, shading.fall as shading_fall,
		trees.gattung_deutsch as tree_gattung, trees.standalter as tree_standalter, trees.baumscheibe as tree_baumscheibe, vitality_index,
		weather_solaranywhere_14d_agg.rainfall_mm_14d_sum as weather_rainfall_mm_14d_sum, 
		weather_solaranywhere_14d_agg.temp_avg_c_14d_avg as weather_temp_avg_c_14d_avg,
		sensor_measurements_agg.median_value as sensor_group_median,
		solar_anywhere.ghi_max_wm2, solar_anywhere.dni_max_wm2, solar_anywhere.dhi_max_wm2, solar_anywhere.ghi_sum_whm2, solar_anywhere.dni_sum_whm2, solar_anywhere.dhi_sum_whm2, 
		solar_anywhere.wind_avg_ms, solar_anywhere.wind_max_ms, solar_anywhere.temp_avg_c, solar_anywhere.temp_max_c, solar_anywhere.rainfall_mm,
		watering_gdk.amount_liters as gdk_amount_liters, watering_sga.amount_liters as sga_amount_liters, 
		tree_radolan_tile.tile_id, radolan_14d_agg.rainfall_mm_14d_sum as radolan_mm_14d_sum,
		sensor_measurements.value as target
FROM private.sensor_measurements
LEFT JOIN public.shading ON public.shading.tree_id = sensor_measurements.tree_id
LEFT JOIN public.trees ON trees.id = sensor_measurements.tree_id
LEFT JOIN private.vitality on vitality.tree_id = sensor_measurements.tree_id
LEFT JOIN private.weather_solaranywhere_14d_agg ON date(sensor_measurements.timestamp) = weather_solaranywhere_14d_agg.date
LEFT JOIN (SELECT * FROM private.weather_tile_measurement WHERE tile_id = 2) as solar_anywhere ON date(sensor_measurements.timestamp) = solar_anywhere.date
LEFT JOIN private.watering_gdk ON (date(sensor_measurements.timestamp) = watering_gdk.date AND sensor_measurements.tree_id = watering_gdk.tree_id)
LEFT JOIN private.watering_sga ON (date(sensor_measurements.timestamp) = watering_sga.date AND sensor_measurements.tree_id = watering_sga.tree_id)
LEFT JOIN tree_radolan_tile ON sensor_measurements.tree_id = tree_radolan_tile.tree_id
LEFT JOIN radolan_14d_agg ON radolan_14d_agg.tile_id = tree_radolan_tile.tile_id AND radolan_14d_agg.date = date(sensor_measurements.timestamp) 
LEFT JOIN private.sensor_measurements_agg ON (date(sensor_measurements.timestamp) = date(sensor_measurements_agg.timestamp) AND sensor_measurements.type_id = sensor_measurements_agg.type_id)
ORDER BY tree_id, nowcast_date DESC;


CREATE MATERIALIZED VIEW public.expert_dashboard AS
SELECT trees.id, CAST(value as int) as saugspannung, timestamp as datum, shading.spring as "Verschattung Frühling", shading.summer as "Verschattung Sommer", shading.fall as "Verschattung Herbst", shading.winter as "Verschattung Winter", art_dtsch, art_bot, bezirk, stammumfg, standalter, baumhoehe, type_id, model_id, kennzeich, standortnr, lat, lng, strname, hausnr
FROM (public.trees
	LEFT JOIN public.nowcast
	   ON trees.id = nowcast.tree_id
	LEFT JOIN public.shading
	  ON trees.id = shading.tree_id)
WHERE (public.trees.street_tree = true) AND (nowcast.timestamp = (SELECT MAX(timestamp) from nowcast));

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
grant select on public.rainfall to qtrees_user;

grant select on public.vector_tiles to authenticator;
grant select on public.vector_tiles to web_anon;
grant select on public.vector_tiles to qtrees_user;

--grant select on public.expert_dashboard to authenticator;
--grant select on public.expert_dashboard to web_anon;
grant select on public.expert_dashboard to qtrees_user;

grant select on public.watering to authenticator;
grant select on public.watering to web_anon;
grant select on public.watering to qtrees_user;

