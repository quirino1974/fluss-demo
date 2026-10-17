-- Job di streaming: copia in tempo reale la tabella Fluss totali_cliente
-- (calcolata dal job totali-per-cliente) nella tabella totali_cliente di PostgreSQL.

CREATE CATALOG fluss_catalog WITH (
    'type' = 'fluss',
    'bootstrap.servers' = 'coordinator-server:9123'
);

USE CATALOG fluss_catalog;

CREATE TABLE IF NOT EXISTS totali_cliente (
    cliente        STRING,
    ordini         BIGINT,
    totale         DECIMAL(12, 2),
    ultimo_ordine  TIMESTAMP(3),
    PRIMARY KEY (cliente) NOT ENFORCED
);

CREATE TEMPORARY TABLE default_catalog.default_database.pg_totali_cliente (
    cliente        STRING,
    ordini         BIGINT,
    totale         DECIMAL(12, 2),
    ultimo_ordine  TIMESTAMP(3),
    PRIMARY KEY (cliente) NOT ENFORCED
) WITH (
    'connector' = 'jdbc',
    'url' = 'jdbc:postgresql://postgres:5432/fluss',
    'table-name' = 'totali_cliente',
    'username' = 'fluss',
    'password' = 'fluss',
    'sink.buffer-flush.interval' = '1s'
);

SET 'execution.checkpointing.interval' = '5s';

SET 'pipeline.name' = 'export-postgres-totali';

INSERT INTO default_catalog.default_database.pg_totali_cliente
SELECT cliente, ordini, totale, ultimo_ordine FROM totali_cliente;
