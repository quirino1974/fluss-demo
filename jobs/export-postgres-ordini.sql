-- Job di streaming: copia in tempo reale la tabella Fluss ordini
-- nella tabella ordini di PostgreSQL (letta da Superset).

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

CREATE TEMPORARY TABLE default_catalog.default_database.pg_ordini (
    id_ordine  BIGINT,
    cliente    STRING,
    importo    DECIMAL(10, 2),
    ts         TIMESTAMP(3),
    PRIMARY KEY (id_ordine) NOT ENFORCED
) WITH (
    'connector' = 'jdbc',
    'url' = 'jdbc:postgresql://postgres:5432/fluss',
    'table-name' = 'ordini',
    'username' = 'fluss',
    'password' = 'fluss',
    'sink.buffer-flush.interval' = '1s'
);

SET 'execution.checkpointing.interval' = '5s';

SET 'pipeline.name' = 'export-postgres-ordini';

INSERT INTO default_catalog.default_database.pg_ordini
SELECT id_ordine, cliente, importo, ts FROM ordini;
