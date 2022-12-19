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


CREATE TABLE "api"."issue_types" (
	"id" int4 NOT NULL,
	"title" text NOT NULL,
	"description" text NOT NULL,
	"image_url" text,
	PRIMARY KEY ("id")
);


CREATE TABLE "api"."issues" (
	"id" int4 NOT NULL,
	"issue_type_id" int4 NOT NULL,
	"created_at" timestamptz NOT NULL DEFAULT now(),
	"tree_id" text NOT NULL,
	PRIMARY KEY ("id")
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
    MESS_DATUM   timestamp NOT NULL,
    QN_3         BIGINT,
    FX           FLOAT(53),
    FM           FLOAT(53),
    QN_4         BIGINT,
    RSK          FLOAT(53),
    RSKF         BIGINT,
    SDK          FLOAT(53),
    SHK_TAG      BIGINT,
    NM           BIGINT,
    VPM          FLOAT(53),
    PM           FLOAT(53),
    TMK          FLOAT(53),
    UPM          FLOAT(53),
    TXK          FLOAT(53),
    TNK          FLOAT(53),
    TGK          FLOAT(53),
    PRIMARY KEY(STATIONS_ID, MESS_DATUM)
);

CREATE TABLE api.radolan (
    id SERIAL PRIMARY KEY,
    rainfall_mm FLOAT(53),
    geometry    geometry(Polygon,4326),
    timestamp   timestamp
);

CREATE TABLE api.shading (
    tree_id TEXT REFERENCES api.trees(id),
    month SMALLINT,
    index FLOAT(53),
    PRIMARY KEY(tree_id, month)
);

CREATE TABLE api.forecast_types (
	id SMALLINT PRIMARY KEY,
	name text NOT NULL
);

CREATE TABLE api.forecast (
	id SERIAL PRIMARY KEY,
	tree_id TEXT REFERENCES api.trees(id),
	forecast_type_id SMALLINT REFERENCES api.forecast_types(id),
	timestamp timestamp,
	value FLOAT(53),
	created_at timestamp,
	model_id text
);

CREATE TABLE api.nowcast (
	id SERIAL PRIMARY KEY,
	tree_id TEXT REFERENCES api.trees(id),
	forecast_type_id SMALLINT REFERENCES api.forecast_types(id),
	timestamp timestamp,
	value FLOAT(53),
	created_at timestamp,
	model_id text
);


insert into api.forecast_types(id, name) values (1, 'saugspannung_30cm');
insert into api.forecast_types(id, name) values (2, 'saugspannung_60cm');
insert into api.forecast_types(id, name) values (3, 'saugspannung_90cm');
insert into api.forecast_types(id, name) values (4, 'saugspannung_stamm');


INSERT INTO "api"."issue_types" ("id", "title", "description", "image_url")
	VALUES (1, 'Hängende Blätter', 'Hängende Blätter könnten ein Mangel am Wasser andeuten. Melde es bitte wenn diesen Baum hängende Blätter hat.', 'https://gxnammfgdsvewxxiuppl.supabase.co/storage/v1/object/sign/issue_images/Screenshot 2022-08-16 at 13.28.03.png?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1cmwiOiJpc3N1ZV9pbWFnZXMvU2NyZWVuc2hvdCAyMDIyLTA4LTE2IGF0IDEzLjI4LjAzLnBuZyIsImlhdCI6MTY2MDc0MjQyOCwiZXhwIjoxOTc2MTAyNDI4fQ.3nppuaaij-MiI6QtAt6mExjme3awUGpKuiUSPt6POhs'),
	(2, 'Insekten Invasion', 'Insekten Invasionen könnten ein Mangel am Wasser andeuten. Melde es bitte wenn diesen Baum eine Insekten Invasion hat.', 'https://gxnammfgdsvewxxiuppl.supabase.co/storage/v1/object/sign/issue_images/invasive-species-stink-bug-2381890735.jpg?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1cmwiOiJpc3N1ZV9pbWFnZXMvaW52YXNpdmUtc3BlY2llcy1zdGluay1idWctMjM4MTg5MDczNS5qcGciLCJpYXQiOjE2NjExNzQzODUsImV4cCI6MTk3NjUzNDM4NX0.iSSxgFlmnZJqlkSwTkNb_1pTHPQepaX2JVzuIXMihuw'),
	(3, 'Baumschaden', 'Baumschäden könnten die Fähigkeit eines Baumes verhindern, Wasser ordentlich aufzunehmen. Melde es bitte wenn diesen Baum einen Schaden hat.', 'https://gxnammfgdsvewxxiuppl.supabase.co/storage/v1/object/sign/issue_images/leitschadbaum012020_1-2445280091.jpg?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1cmwiOiJpc3N1ZV9pbWFnZXMvbGVpdHNjaGFkYmF1bTAxMjAyMF8xLTI0NDUyODAwOTEuanBnIiwiaWF0IjoxNjYxMTc0NzE2LCJleHAiOjE5NzY1MzQ3MTZ9.nIqml2B2RVMVib7BPkRea0CYRc307Jmppx0yM30HEPU');
