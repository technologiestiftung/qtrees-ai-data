CREATE EXTENSION postgis;
CREATE EXTENSION fuzzystrmatch;
CREATE EXTENSION postgis_tiger_geocoder;
CREATE EXTENSION postgis_topology;

CREATE SCHEMA api;
--
CREATE TABLE api.trees (
    gml_id TEXT PRIMARY KEY,
    baumid TEXT,
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
     gml_id          TEXT, -- this not the tree id
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


--CREATE VIEW api.train_data AS
--    SELECT *
--    FROM films
--    WHERE kind = 'Comedy';

CREATE TABLE api.user_info (
    id SERIAL PRIMARY KEY,
    gml_id TEXT REFERENCES api.trees (gml_id),
    nutzer_id TEXT,
    merkmal TEXT,
    wert TEXT
);

CREATE TABLE api.weather_stations (
    Stations_id   BIGINT PRIMARY KEY,
    von_datum     DATE,
    bis_datum     DATE,
    Stationshoehe bigint,
    geoBreite     FLOAT(53),
    geoLaenge     FLOAT(53),
    Stationsname  text,
    Bundesland    text,
    geometry geometry(POINT,4326)
);

CREATE TABLE api.weather (
    STATIONS_ID  BIGINT NOT NULL,
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
    gml_id TEXT REFERENCES api.trees(gml_id),
    month SMALLINT,
    index FLOAT(53),
    PRIMARY KEY(gml_id, month)
);

CREATE TABLE api.forecast_types (
	id SMALLINT PRIMARY KEY,
	name text NOT NULL
);

CREATE TABLE api.forecast (
	id SERIAL PRIMARY KEY,
	baum_id TEXT REFERENCES api.trees(gml_id),
	type_id SMALLINT REFERENCES api.forecast_types(id),
	timestamp timestamp,
	value FLOAT(53),
	created_at timestamp,
	model_id text
);

CREATE TABLE api.nowcast (
	id SERIAL PRIMARY KEY,
	baum_id TEXT REFERENCES api.trees(gml_id),
	type_id SMALLINT REFERENCES api.forecast_types(id),
	timestamp timestamp,
	value FLOAT(53),
	created_at timestamp,
	model_id text
);


insert into api.forecast_types(id, name) values (1, 'saugspannung_30cm');
insert into api.forecast_types(id, name) values (2, 'saugspannung_60cm');
insert into api.forecast_types(id, name) values (3, 'saugspannung_90cm');
insert into api.forecast_types(id, name) values (4, 'saugspannung_stamm');
