CREATE EXTENSION postgis;
CREATE EXTENSION fuzzystrmatch;
CREATE EXTENSION postgis_tiger_geocoder;
CREATE EXTENSION postgis_topology;

CREATE SCHEMA api;
--
CREATE TABLE api.trees (
    id TEXT PRIMARY KEY,
    standortnr TEXT,
    kennzeich TEXT,
    namenr TEXT,
    art_dtsch TEXT,
    art_bot TEXT,
    gattung_deutsch TEXT,
    gattung TEXT,
    strname TEXT,
    hausnr TEXT,
    pflanzjahr FLOAT(53),
    standalter FLOAT(53),
    stammumfg FLOAT(53),
    baumhoehe FLOAT(53),
    bezirk TEXT,
    eigentuemer TEXT,
    zusatz TEXT,
    kronedurch FLOAT(53),
    geometry geometry(POINT,4326),
    lat FLOAT(53),
    lng FLOAT(53),
    created_at DATE,
    updated_at DATE,
    street_tree BOOLEAN
);

CREATE TABLE api.soil (
     id              TEXT PRIMARY KEY,
     schl5           BIGINT,
     nutz            FLOAT(53),
     nutz_bez        TEXT,
     vgradstufe      FLOAT(53),
     vgradstufe_bez  TEXT,
     boges_neu5      FLOAT(53),
     btyp            TEXT,
     bg_alt          TEXT,
     nutzgenese      TEXT,
     ausgangsm       TEXT,
     geomeinh        FLOAT(53),
     geomeinh_bez    TEXT,
     aus_bg          FLOAT(53),
     aus_bg_bez      TEXT,
     antro_bg        FLOAT(53),
     antro_bg_bez    TEXT,
     torf_bg         FLOAT(53),
     torf_bg_bez     TEXT,
     torf_klas       FLOAT(53),
     flur            FLOAT(53),
     flurstufe       FLOAT(53),
     flurstufe_bez   TEXT,
     flurklasse      FLOAT(53),
     flurklasse_bez  TEXT,
     bnbg_ob_h       TEXT,
     bnbg_ob_h_bez   TEXT,
     bnbg_ub_h       TEXT,
     bnbg_ub_h_bez   TEXT,
     bnbg_ob         TEXT,
     bngb_ob_bez     TEXT,
     bnbg_ub         TEXT,
     bnbg_ub_bez     TEXT,
     bart_gr         FLOAT(53),
     sg_ob           TEXT,
     sg_ob_bez       TEXT,
     sg_ub           TEXT,
     sg_ub_bez       TEXT,
     sg_klas         FLOAT(53),
     sg_klas_bez     TEXT,
     btyp_ka3        TEXT,
     btyp_ka3_bez    TEXT,
     btyp_ka4        TEXT,
     btyp_ka4_bez    TEXT,
     bform_ka5       TEXT,
     bform_ka5_bez   TEXT,
     torf_ob         TEXT,
     torf_ob_bez     TEXT,
     torf_klas_bez   TEXT,
     torf_ub         TEXT,
     torf_ub_bez     TEXT,
     geometry        geometry(MultiPolygon,4326),
     created_at      DATE,
     updated_at      DATE
);

CREATE TABLE api.user_info (
    id SERIAL PRIMARY KEY,
    gml_id TEXT REFERENCES api.trees (gml_id),
    nutzer_id TEXT,
    merkmal TEXT,
    wert TEXT
);

CREATE TABLE api.weather_stations (
    id   BIGINT PRIMARY KEY,
    von_datum     DATE,
    bis_datum     DATE,
    Stationshoehe bigint,
    lat     FLOAT(53),
    lon     FLOAT(53),
    Stationsname  text,
    Bundesland    text,
    geometry geometry(POINT,4326)
);

CREATE TABLE api.weather (
    STATIONS_ID  BIGINT REFERENCES api.weather_stations (id),
    timestamp   timestamp NOT NULL,
    QN_3         BIGINT,
    wind_max_ms  FLOAT(53),
    wind_mean_ms FLOAT(53),
    QN_4         BIGINT,
    rainfall_mm  FLOAT(53),
    RSKF         BIGINT,
    SDK          FLOAT(53),
    SHK_TAG      BIGINT,
    NM           BIGINT,
    VPM          FLOAT(53),
    PM           FLOAT(53),
    temp_avg_c   FLOAT(53),
    UPM          FLOAT(53),
    temp_max_c   FLOAT(53),
    TNK          FLOAT(53),
    TGK          FLOAT(53),
    PRIMARY KEY(STATIONS_ID, timestamp)
);

CREATE TABLE api.radolan (
    grid_id  BIGINT NOT NULL,
    timestamp   timestamp NOT NULL,
    rainfall_mm FLOAT(53),
    PRIMARY KEY(grid_id, timestamp)
);

CREATE TABLE api.radolan_grid (
    id BIGINT PRIMARY KEY,
    geometry  geometry(Polygon,4326)
);

CREATE TABLE api.tree_radolan (
    tree_id TEXT REFERENCES api.trees(id),
    grid_id  BIGINT REFERENCES api.radolan_grid(id),
    PRIMARY KEY(tree_id, grid_id)
);

CREATE TABLE api.tree_devices (
    tree_id TEXT REFERENCES api.trees(id),
    customer_id BIGINT REFERENCES api.customers(id),
    device_id  BIGINT,
    site_id BIGINT
    PRIMARY KEY(tree_id)
);


CREATE TABLE api.shading (
    tree_id TEXT REFERENCES api.trees(id),
    month SMALLINT,
    index FLOAT(53),
    PRIMARY KEY(tree_id, month)
);

CREATE TABLE api.sensor_types (
	id SMALLINT PRIMARY KEY,
	name text NOT NULL
);

CREATE TABLE api.customers (
	id SMALLINT PRIMARY KEY,
	name text NOT NULL
);

CREATE TABLE api.forecast (
	id SERIAL PRIMARY KEY,
	tree_id TEXT REFERENCES api.trees(id),
	type_id SMALLINT REFERENCES api.sensor_types(id),
	timestamp timestamp,
	value FLOAT(53),
	created_at timestamp,
	model_id text
);

CREATE TABLE api.nowcast (
	id SERIAL PRIMARY KEY,
	tree_id TEXT REFERENCES api.trees(id),
	type_id SMALLINT REFERENCES api.sensor_types(id),
	timestamp timestamp,
	value FLOAT(53),
	created_at timestamp,
	model_id text
);

-- views
CREATE VIEW api.shading_wide AS
SELECT tree_id, 
       MAX(index) FILTER (WHERE month = 3) AS spring,
       MAX(index) FILTER (WHERE month = 6) AS summer,
       MAX(index) FILTER (WHERE month = 9) AS fall,
       MAX(index) FILTER (WHERE month = 12) AS winter
FROM api.shading
GROUP BY tree_id;

CREATE VIEW api.weather_14d_agg AS
select timestamp, 
		sum(rainfall_mm) OVER(ORDER BY timestamp ROWS BETWEEN 13 PRECEDING AND CURRENT ROW ) as rainfall_mm_14d_sum, 
		avg(temp_avg_c) OVER(ORDER BY timestamp ROWS BETWEEN 13 PRECEDING AND CURRENT ROW ) as temp_avg_c_14d_avg,
		avg(wind_mean_ms) OVER(ORDER BY timestamp ROWS BETWEEN 13 PRECEDING AND CURRENT ROW ) as wind_avg_ms_14d_avg,
		avg(temp_max_c) OVER(ORDER BY timestamp ROWS BETWEEN 13 PRECEDING AND CURRENT ROW ) as temp_max_c_14d_avg,
		avg(wind_max_ms) OVER(ORDER BY timestamp ROWS BETWEEN 13 PRECEDING AND CURRENT ROW ) as wind_max_ms_14d_avg
from api.weather
where stations_id = 433;

CREATE VIEW api.training_data AS
SELECT sensor_measurements.tree_id, sensor_measurements.sensor_type, sensor_measurements.timestamp, sensor_measurements.value,
		shading_wide.winter, shading_wide.spring, shading_wide.summer, shading_wide.fall,
		trees.gattung_deutsch, trees.standalter,
		weather_14d_agg.temp_avg_c_14d_avg, weather_14d_agg.wind_avg_ms_14d_avg, weather_14d_agg.temp_max_c_14d_avg, weather_14d_agg.wind_max_ms_14d_avg 
FROM api.sensor_measurements
LEFT JOIN api.shading_wide ON api.shading_wide.tree_id = sensor_measurements.tree_id
LEFT JOIN api.trees ON trees.id = sensor_measurements.tree_id
LEFT JOIN api.weather_14d_agg ON sensor_measurements.timestamp = weather_14d_agg.timestamp
ORDER BY timestamp DESC;

CREATE VIEW api.test_data AS
SELECT trees.id, trees.gattung_deutsch, trees.standalter,
		shading_wide.winter, shading_wide.spring, shading_wide.summer, shading_wide.fall,
		(SELECT weather.rainfall_mm  FROM api.weather WHERE timestamp = (SELECT current_date - INTEGER '1')) as rainfall_mm,
		(SELECT weather.temp_avg  FROM api.weather WHERE timestamp = (SELECT current_date - INTEGER '1')) as temp_mean,
		(SELECT weather.temp_max FROM api.weather WHERE timestamp = (SELECT current_date - INTEGER '1')) as temp_max
FROM api.trees
LEFT JOIN api.shading_wide ON api.shading_wide.tree_id = api.trees.id;


insert into api.sensor_types(id, name) values (1, 'saugspannung_30cm');
insert into api.sensor_types(id, name) values (2, 'saugspannung_60cm');
insert into api.sensor_types(id, name) values (3, 'saugspannung_90cm');
insert into api.sensor_types(id, name) values (4, 'saugspannung_stamm');

insert into api.customers(id, name) values (2, "Mitte")
insert into api.customers(id, name) values (3, "Neukölln")