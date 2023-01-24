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

CREATE TABLE public.soil (
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


CREATE TABLE "public"."issue_types" (
	"id" serial,
	"title" text NOT NULL,
	"description" text NOT NULL,
	"image_url" text,
	PRIMARY KEY ("id")
);


CREATE TABLE "public"."issues" (
	"id" serial,
	"issue_type_id" int4 NOT NULL REFERENCES public.issue_types (id),
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
    PRIMARY KEY(stations_id, timestamp)
);

CREATE TABLE public.radolan (
    tile_id  BIGINT REFERENCES public.radolan_tiles(id),
    timestamp   timestamp NOT NULL,
    rainfall_mm FLOAT(53),
    PRIMARY KEY(tile_id, timestamp)
);

CREATE TABLE public.radolan_tiles (
    id BIGINT PRIMARY KEY,
    geometry  geometry(Polygon,4326)
);

CREATE TABLE public.shading (
    tree_id TEXT REFERENCES public.trees(id),
    month SMALLINT,
    index FLOAT(53),
    PRIMARY KEY(tree_id, month)
);

CREATE TABLE public.sensor_types (
	id SERIAL PRIMARY KEY,
	name text NOT NULL
);

CREATE TABLE public.forecast (
	id SERIAL PRIMARY KEY,
	tree_id TEXT REFERENCES public.trees(id),
	type_id SMALLINT REFERENCES public.sensor_types(id),
	timestamp timestamp,
	value FLOAT(53),
	created_at timestamp,
	model_id text
);

CREATE TABLE public.nowcast (
	id SERIAL PRIMARY KEY,
	tree_id TEXT REFERENCES public.trees(id),
	type_id SMALLINT REFERENCES public.sensor_types(id),
	timestamp timestamp,
	value FLOAT(53),
	created_at timestamp,
	model_id text
);

insert into public.sensor_types(id, name) values (1, 'saugspannung_30cm');
insert into public.sensor_types(id, name) values (2, 'saugspannung_60cm');
insert into public.sensor_types(id, name) values (3, 'saugspannung_90cm');
insert into public.sensor_types(id, name) values (4, 'saugspannung_stamm');


INSERT INTO "public"."issue_types" ("id", "title", "description", "image_url")
	VALUES (1, 'Hängende Blätter', 'Hängende Blätter könnten ein Mangel am Wasser andeuten. Melde es bitte wenn diesen Baum hängende Blätter hat.', 'https://gxnammfgdsvewxxiuppl.supabase.co/storage/v1/object/sign/issue_images/Screenshot 2022-08-16 at 13.28.03.png?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1cmwiOiJpc3N1ZV9pbWFnZXMvU2NyZWVuc2hvdCAyMDIyLTA4LTE2IGF0IDEzLjI4LjAzLnBuZyIsImlhdCI6MTY2MDc0MjQyOCwiZXhwIjoxOTc2MTAyNDI4fQ.3nppuaaij-MiI6QtAt6mExjme3awUGpKuiUSPt6POhs'),
	(2, 'Insekten Invasion', 'Insekten Invasionen könnten ein Mangel am Wasser andeuten. Melde es bitte wenn diesen Baum eine Insekten Invasion hat.', 'https://gxnammfgdsvewxxiuppl.supabase.co/storage/v1/object/sign/issue_images/invasive-species-stink-bug-2381890735.jpg?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1cmwiOiJpc3N1ZV9pbWFnZXMvaW52YXNpdmUtc3BlY2llcy1zdGluay1idWctMjM4MTg5MDczNS5qcGciLCJpYXQiOjE2NjExNzQzODUsImV4cCI6MTk3NjUzNDM4NX0.iSSxgFlmnZJqlkSwTkNb_1pTHPQepaX2JVzuIXMihuw'),
	(3, 'Baumschaden', 'Baumschäden könnten die Fähigkeit eines Baumes verhindern, Wasser ordentlich aufzunehmen. Melde es bitte wenn diesen Baum einen Schaden hat.', 'https://gxnammfgdsvewxxiuppl.supabase.co/storage/v1/object/sign/issue_images/leitschadbaum012020_1-2445280091.jpg?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1cmwiOiJpc3N1ZV9pbWFnZXMvbGVpdHNjaGFkYmF1bTAxMjAyMF8xLTI0NDUyODAwOTEuanBnIiwiaWF0IjoxNjYxMTc0NzE2LCJleHAiOjE5NzY1MzQ3MTZ9.nIqml2B2RVMVib7BPkRea0CYRc307Jmppx0yM30HEPU');


CREATE SCHEMA private;
GRANT ALL ON SCHEMA private TO postgres;

CREATE TABLE private.customers (
	id SMALLINT PRIMARY KEY,
	name text NOT NULL
);

CREATE TABLE private.tree_devices (
    tree_id TEXT REFERENCES public.trees(id),
    customer_id BIGINT REFERENCES private.customers(id),
    device_id  BIGINT,
    site_id BIGINT,
    PRIMARY KEY(tree_id, customer_id, device_id, site_id)
);

CREATE TABLE private.sensor_measurements (
	tree_id TEXT REFERENCES public.trees(id),
    type_id SMALLINT REFERENCES public.sensor_types(id),
	sensor_id SMALLINT,
	timestamp timestamp,
	value FLOAT(53),
    PRIMARY KEY(tree_id, type_id, timestamp)
);

insert into private.customers(id, name) values (2, 'Mitte');
insert into private.customers(id, name) values (3, 'Neukölln');