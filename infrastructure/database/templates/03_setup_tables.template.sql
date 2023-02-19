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
    created_at DATE,
    updated_at DATE,
    street_tree BOOLEAN, 
    baumscheibe REAL
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
     created_at      DATE,
     updated_at      DATE
);


CREATE TABLE "public"."issue_types" (
	"id" serial,
	"title" text NOT NULL,
	"description" text NOT NULL,
	"image_url" text,
	PRIMARY KEY ("id")
);


CREATE TABLE "public"."issues" (
	"id" serial,
	"issue_type_id" INTEGER NOT NULL REFERENCES public.issue_types (id),
	"created_at" timestamptz NOT NULL DEFAULT now(),
	"tree_id" text NOT NULL REFERENCES public.trees (id),
	PRIMARY KEY ("id")
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
    wind_mean_ms REAL,
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

CREATE TABLE public.sensor_types (
	id SERIAL PRIMARY KEY,
	name text NOT NULL
);

CREATE TABLE public.forecast (
	id SERIAL PRIMARY KEY,
	tree_id TEXT REFERENCES public.trees(id),
	type_id INTEGER REFERENCES public.sensor_types(id),
	timestamp timestamp,
	value REAL,
	created_at timestamp,
	model_id text
);

CREATE TABLE public.nowcast (
	id SERIAL PRIMARY KEY,
	tree_id TEXT REFERENCES public.trees(id),
	type_id INTEGER REFERENCES public.sensor_types(id),
	timestamp timestamp,
	value REAL,
	created_at timestamp,
	model_id text
);

CREATE INDEX idx_nowcast_tree_id
ON nowcast(tree_id);
CREATE INDEX idx_forecast_tree_id
ON forecast(tree_id);

insert into public.sensor_types(id, name) values (1, 'saugspannung_30cm');
insert into public.sensor_types(id, name) values (2, 'saugspannung_60cm');
insert into public.sensor_types(id, name) values (3, 'saugspannung_90cm');
insert into public.sensor_types(id, name) values (4, 'saugspannung_stamm');

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
    valid_from_date DATE,
    valid_to_date DATE,
    PRIMARY KEY(tree_id, customer_id, device_id)
);

CREATE TABLE private.vitality (
    tree_id TEXT REFERENCES public.trees(id),
    vitality_index REAL,
    PRIMARY KEY(tree_id)
);

CREATE TABLE private.sensor_measurements (
	tree_id TEXT REFERENCES public.trees(id),
    type_id INTEGER REFERENCES public.sensor_types(id),
	sensor_id INTEGER,
	timestamp timestamp,
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
    tree_id TEXT REFERENCES public.trees(id),
    amount_liters REAL,
    date DATE,
    PRIMARY KEY(tree_id, date)
);

insert into private.customers(id, name) values (2, 'Mitte');
insert into private.customers(id, name) values (3, 'Neukölln');
