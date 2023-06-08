CREATE EXTENSION postgis;
CREATE EXTENSION fuzzystrmatch;
CREATE EXTENSION postgis_tiger_geocoder;
CREATE EXTENSION postgis_topology;

--
CREATE TABLE public.trees (
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
    pflanzjahr REAL,
    standalter REAL,
    stammumfg REAL,
    baumhoehe REAL,
    bezirk TEXT,
    eigentuemer TEXT,
    zusatz TEXT,
    kronedurch REAL,
    geometry geometry(POINT,4326),
    lat FLOAT(53),
    lng FLOAT(53),
    created_at timestamptz,
    updated_at timestamptz,
    street_tree BOOLEAN
);

CREATE TABLE public.soil (
     id              TEXT PRIMARY KEY,
     schl5           BIGINT,
     nutz            REAL,
     nutz_bez        TEXT,
     vgradstufe      REAL,
     vgradstufe_bez  TEXT,
     boges_neu5      REAL,
     btyp            TEXT,
     bg_alt          TEXT,
     nutzgenese      TEXT,
     ausgangsm       TEXT,
     geomeinh        REAL,
     geomeinh_bez    TEXT,
     aus_bg          REAL,
     aus_bg_bez      TEXT,
     antro_bg        REAL,
     antro_bg_bez    TEXT,
     torf_bg         REAL,
     torf_bg_bez     TEXT,
     torf_klas       REAL,
     flur            REAL,
     flurstufe       REAL,
     flurstufe_bez   TEXT,
     flurklasse      REAL,
     flurklasse_bez  TEXT,
     bnbg_ob_h       TEXT,
     bnbg_ob_h_bez   TEXT,
     bnbg_ub_h       TEXT,
     bnbg_ub_h_bez   TEXT,
     bnbg_ob         TEXT,
     bngb_ob_bez     TEXT,
     bnbg_ub         TEXT,
     bnbg_ub_bez     TEXT,
     bart_gr         REAL,
     sg_ob           TEXT,
     sg_ob_bez       TEXT,
     sg_ub           TEXT,
     sg_ub_bez       TEXT,
     sg_klas         REAL,
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
     created_at      timestamptz,
     updated_at      timestamptz
);


CREATE TABLE public.issue_types (
	id serial,
	title text NOT NULL,
	description text NOT NULL,
	image_url text,
	PRIMARY KEY (id)
);


CREATE TABLE public.issues (
	id serial,
	issue_type_id INTEGER NOT NULL REFERENCES public.issue_types (id),
	created_at timestamptz NOT NULL DEFAULT now(),
	tree_id text NOT NULL REFERENCES public.trees (id),
	PRIMARY KEY (id)
);

CREATE TABLE public.weather_stations (
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

CREATE TABLE public.weather (
    stations_id  BIGINT REFERENCES public.weather_stations (id),
    date   DATE NOT NULL,
    QN_3         BIGINT,
    wind_max_ms  REAL,
    wind_avg_ms REAL,
    QN_4         BIGINT,
    rainfall_mm  REAL,
    RSKF         BIGINT,
    SDK          REAL,
    SHK_TAG      BIGINT,
    NM           BIGINT,
    VPM          REAL,
    PM           REAL,
    temp_avg_c   REAL,
    UPM          REAL,
    temp_max_c   REAL,
    TNK          REAL,
    TGK          REAL,
    PRIMARY KEY(stations_id, date)
);

CREATE TABLE public.radolan_tiles (
    id BIGINT PRIMARY KEY,
    geometry  geometry(Polygon,4326)
);

CREATE TABLE public.radolan (
    tile_id  BIGINT REFERENCES public.radolan_tiles(id),
    date   DATE NOT NULL,
    rainfall_mm REAL,
    rainfall_max_mm REAL,
    PRIMARY KEY(tile_id, date)
);

CREATE TABLE public.shading (
    tree_id TEXT REFERENCES public.trees(id),
    spring REAL,
    summer REAL,
    fall REAL,
    winter REAL,
    PRIMARY KEY(tree_id)
);

CREATE TABLE public.shading_monthly (
    tree_id TEXT REFERENCES public.trees(id),
    january REAL,
    february REAL,
    march REAL,
    april REAL,
    may REAL,
    june REAL,
    july REAL,
    august REAL,
    september REAL,
    october REAL,
    november REAL,
    december REAL,
    PRIMARY KEY(tree_id)
);

CREATE TABLE public.sensor_types (
	id SERIAL PRIMARY KEY,
	name text NOT NULL
);

CREATE TABLE public.forecast (
	id SERIAL PRIMARY KEY,
	tree_id TEXT REFERENCES public.trees(id),
	type_id INTEGER REFERENCES public.sensor_types(id),
	timestamp timestamptz,
	value REAL,
	created_at timestamptz NOT NULL DEFAULT now(),
	model_id text
);

CREATE TABLE public.nowcast (
	id SERIAL PRIMARY KEY,
	tree_id TEXT REFERENCES public.trees(id),
	type_id INTEGER REFERENCES public.sensor_types(id),
	timestamp timestamptz,
	value REAL,
	created_at timestamptz NOT NULL DEFAULT now(),
	model_id text
);

CREATE OR REPLACE VIEW public.latest_nowcast AS
SELECT DISTINCT ON (tree_id, type_id)
    id,
    tree_id,
    type_id,
    timestamp,
    value,
    created_at,
    model_id
FROM public.nowcast
ORDER BY tree_id, type_id, timestamp DESC;

CREATE OR REPLACE VIEW public.latest_forecast AS
SELECT *
FROM crosstab(
    $$
    SELECT
        tree_id,
        type_id,
        row_number() OVER (PARTITION BY tree_id, type_id ORDER BY timestamp) AS day,
        value
    FROM public.nowcast
    ORDER BY 1, 2, 3
    $$,
    $$
    SELECT generate_series(1, 14)
    $$
) AS ct (tree_id TEXT, type_id INTEGER, day1_timestamp timestamptz, day1 REAL, day2 REAL, day3 REAL, day4 REAL, day5 REAL, day6 REAL, day7 REAL, day8 REAL, day9 REAL, day10 REAL, day11 REAL, day12 REAL, day13 REAL, day14 REAL);


CREATE INDEX idx_nowcast_tree_id
ON nowcast(tree_id);
CREATE INDEX idx_forecast_tree_id
ON forecast(tree_id);

insert into public.sensor_types(id, name) values (1, 'saugspannung_30cm');
insert into public.sensor_types(id, name) values (2, 'saugspannung_60cm');
insert into public.sensor_types(id, name) values (3, 'saugspannung_90cm');
insert into public.sensor_types(id, name) values (4, 'saugspannung_mittel');
insert into public.sensor_types(id, name) values (5, 'saugspannung_stamm');

INSERT INTO "public"."issue_types" ( "title", "description", "image_url") VALUES
( 'Missnutzung der Baumscheibe', 'Die Baumscheibe (nicht versiegelte Fläche) am Standort eines Baums wir oft durch falsch parkende Autos, illegalen Müll-Entsorgungen, wie bspw.: alte Waschmaschinen oder Bauschutt, missbraucht. Melde uns bitte, wenn die Baumscheibe seit längerem zugestellt ist.', '/images/issues/missnutzung-baumscheibe.jpg'),
( 'Baumschäden', 'Baumschäden, wie bspw. abgeknickte Äste, stellen eine Gefahr für den Straßenraum dar und können die Vitalität eines Baumes nachhaltig einschränken. Melde uns bitte, wenn dieser Baum einen Schaden hat.', '/images/issues/baumschaeden.jpg');

CREATE SCHEMA private;
GRANT ALL ON SCHEMA private TO postgres;

CREATE TABLE private.customers (
	id INTEGER PRIMARY KEY,
	name text NOT NULL
);

CREATE TABLE private.tree_devices (
    tree_id TEXT REFERENCES public.trees(id),
    customer_id INTEGER REFERENCES private.customers(id),
    device_id  BIGINT,
    site_id BIGINT,
    valid_from_date DATE,
    valid_to_date DATE,
    PRIMARY KEY(tree_id, customer_id, device_id)
);

CREATE TABLE private.tree_private (
    tree_id TEXT, -- ommited REFERENCES public.trees(id) as we allow trees that are not (yet) in trees table
    vitality_index REAL,
    baumscheibe REAL,
    PRIMARY KEY(tree_id)
);

CREATE TABLE private.sensor_measurements (
	tree_id TEXT REFERENCES public.trees(id),
    type_id INTEGER REFERENCES public.sensor_types(id),
	sensor_id INTEGER,
	timestamp timestamptz,
	value REAL,
    PRIMARY KEY(tree_id, type_id, timestamp)
);

CREATE TABLE private.watering_gdk (
    tree_id TEXT REFERENCES public.trees(id),
    amount_liters REAL,
    date DATE,
    PRIMARY KEY(tree_id, date)
);

CREATE TABLE private.watering_sga (
    tree_id TEXT, -- ommited REFERENCES public.trees(id) as we allow trees that are not (yet) in trees table
    amount_liters REAL,
    date DATE,
    PRIMARY KEY(tree_id, date)
);

insert into private.customers(id, name) values (2, 'Mitte');
insert into private.customers(id, name) values (3, 'Neukölln');


CREATE TABLE private.weather_tiles (
    id BIGINT PRIMARY KEY,
    lat FLOAT(53),
    lng FLOAT(53),
    geometry  geometry(Polygon,4326)
);

CREATE TABLE private.weather_tile_measurement (
    tile_id  BIGINT REFERENCES private.weather_tiles (id),
    date DATE NOT NULL,
    ghi_max_wm2 REAL,
    dni_max_wm2 REAL,
    dhi_max_wm2 REAL,
    ghi_sum_whm2 REAL,
    dni_sum_whm2 REAL,
    dhi_sum_whm2 REAL,
    wind_avg_ms REAL,
    wind_max_ms REAL,
    temp_avg_c   REAL,
    temp_max_c   REAL,
    rainfall_mm  REAL,
    PRIMARY KEY(tile_id, date)
);

CREATE TABLE private.weather_tile_forecast (
    tile_id  BIGINT REFERENCES private.weather_tiles (id),
    date DATE NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    ghi_max_wm2 REAL,
    dni_max_wm2 REAL,
    dhi_max_wm2 REAL,
    ghi_sum_whm2 REAL,
    dni_sum_whm2 REAL,
    dhi_sum_whm2 REAL,
    wind_avg_ms REAL,
    wind_max_ms REAL,
    temp_avg_c   REAL,
    temp_max_c   REAL,
    rainfall_mm  REAL,
    PRIMARY KEY(tile_id, date, created_at)
);


-- it's not really sqare. So may adjust at some time.
INSERT INTO private.weather_tiles(id, lng, lat, geometry)
VALUES (2, 13.367615, 52.526836, 'POLYGON ((13.309444 52.572556, 13.425786 52.572556, 13.425786 52.472556, 13.309444 52.472556, 13.309444 52.572556))'),
       (3, 13.447711, 52.448092, 'POLYGON ((13.377733038944818 52.49809199460378, 13.517688961055182 52.4980919946037, 13.517532424761926 52.39809199460377, 13.377876575238076 52.39809199460377, 13.377733038944818 52.49809199460378))');
