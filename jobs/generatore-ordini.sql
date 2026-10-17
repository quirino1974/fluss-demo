-- Job di streaming: genera un ordine casuale al secondo e lo scrive nella tabella ordini.
-- Serve solo a vedere Flink al lavoro; si ferma con: flink_jobs.py stop generatore-ordini

CREATE CATALOG fluss_catalog WITH (
    'type' = 'fluss',
    'bootstrap.servers' = 'coordinator-server:9123'
);

USE CATALOG fluss_catalog;

CREATE TABLE IF NOT EXISTS ordini (
    id_ordine  BIGINT,
    cliente    STRING,
    importo    DECIMAL(10, 2),
    ts         TIMESTAMP(3),
    PRIMARY KEY (id_ordine) NOT ENFORCED
);

-- Sorgente casuale di Flink (tabella temporanea, vive solo in questa sessione)
CREATE TEMPORARY TABLE default_catalog.default_database.gen_ordini (
    id_ordine  BIGINT,
    n          INT,
    importo    DOUBLE
) WITH (
    'connector' = 'datagen',
    'rows-per-second' = '1',
    'fields.id_ordine.min' = '1',
    'fields.id_ordine.max' = '99999999999',
    'fields.n.min' = '1',
    'fields.n.max' = '5',
    'fields.importo.min' = '5',
    'fields.importo.max' = '205'
);

SET 'table.local-time-zone' = 'Europe/Rome';

SET 'execution.checkpointing.interval' = '5s';

SET 'pipeline.name' = 'generatore-ordini';

INSERT INTO ordini
SELECT
    id_ordine,
    ARRAY['Rossi', 'Bianchi', 'Verdi', 'Russo', 'Ferrari'][n],
    CAST(importo AS DECIMAL(10, 2)),
    CAST(LOCALTIMESTAMP AS TIMESTAMP(3))
FROM default_catalog.default_database.gen_ordini;
