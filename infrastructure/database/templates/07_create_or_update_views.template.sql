
-- views
CREATE OR REPLACE VIEW api.shading_wide AS
SELECT tree_id, 
       MAX(index) FILTER (WHERE month = 3) AS spring,
       MAX(index) FILTER (WHERE month = 6) AS summer,
       MAX(index) FILTER (WHERE month = 9) AS fall,
       MAX(index) FILTER (WHERE month = 12) AS winter
FROM api.shading
GROUP BY tree_id;

CREATE OR REPLACE VIEW api.weather_14d_agg AS
select timestamp, 
		sum(rainfall_mm) OVER(ORDER BY timestamp ROWS BETWEEN 13 PRECEDING AND CURRENT ROW ) as rainfall_mm_14d_sum, 
		avg(temp_avg_c) OVER(ORDER BY timestamp ROWS BETWEEN 13 PRECEDING AND CURRENT ROW ) as temp_avg_c_14d_avg,
		avg(wind_mean_ms) OVER(ORDER BY timestamp ROWS BETWEEN 13 PRECEDING AND CURRENT ROW ) as wind_avg_ms_14d_avg,
		avg(temp_max_c) OVER(ORDER BY timestamp ROWS BETWEEN 13 PRECEDING AND CURRENT ROW ) as temp_max_c_14d_avg,
		avg(wind_max_ms) OVER(ORDER BY timestamp ROWS BETWEEN 13 PRECEDING AND CURRENT ROW ) as wind_max_ms_14d_avg
from api.weather
where stations_id = 433;

CREATE OR REPLACE VIEW api.tree_radolan_tile AS
select trees.id as tree_id, tiles.id as tile_id
from api.trees as trees
join api.radolan_tiles as tiles
ON ST_Contains(tiles.geometry, trees.geometry);

CREATE OR REPLACE VIEW api.radolan_14d_agg AS
SELECT radolan.timestamp, radolan.tile_id,
SUM(radolan.rainfall_mm) OVER (partition by radolan.tile_id ORDER BY radolan.timestamp ROWS BETWEEN 13 PRECEDING AND CURRENT ROW) AS rainfall_mm_14d_sum
FROM api.radolan;

CREATE OR REPLACE VIEW api.training_data AS
SELECT sensor_measurements.tree_id, sensor_measurements.sensor_id, sensor_measurements.timestamp, sensor_measurements.value,
		shading_wide.winter, shading_wide.spring, shading_wide.summer, shading_wide.fall,
		trees.gattung_deutsch, trees.standalter,
		weather_14d_agg.temp_avg_c_14d_avg, weather_14d_agg.wind_avg_ms_14d_avg, weather_14d_agg.temp_max_c_14d_avg, weather_14d_agg.wind_max_ms_14d_avg 
FROM api.sensor_measurements
LEFT JOIN api.shading_wide ON api.shading_wide.tree_id = sensor_measurements.tree_id
LEFT JOIN api.trees ON trees.id = sensor_measurements.tree_id
LEFT JOIN api.weather_14d_agg ON sensor_measurements.timestamp = weather_14d_agg.timestamp
ORDER BY timestamp DESC;

CREATE OR REPLACE VIEW api.test_data AS
SELECT trees.id, trees.gattung_deutsch, trees.standalter,
		shading_wide.winter, shading_wide.spring, shading_wide.summer, shading_wide.fall,
		(SELECT weather.rainfall_mm  FROM api.weather WHERE timestamp = (SELECT current_date - INTEGER '1')) as rainfall_mm,
		(SELECT weather.temp_avg_c  FROM api.weather WHERE timestamp = (SELECT current_date - INTEGER '1')) as temp_mean,
		(SELECT weather.temp_max_c FROM api.weather WHERE timestamp = (SELECT current_date - INTEGER '1')) as temp_max
FROM api.trees
LEFT JOIN api.shading_wide ON api.shading_wide.tree_id = api.trees.id;