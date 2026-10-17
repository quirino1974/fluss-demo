-- Job di streaming: legge in continuo le modifiche della tabella ordini
-- e tiene aggiornata la tabella totali_cliente (chiave primaria = cliente).

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

CREATE TABLE IF NOT EXISTS totali_cliente (
    cliente        STRING,
    ordini         BIGINT,
    totale         DECIMAL(12, 2),
    ultimo_ordine  TIMESTAMP(3),
    PRIMARY KEY (cliente) NOT ENFORCED
);

SET 'execution.checkpointing.interval' = '5s';

SET 'pipeline.name' = 'totali-per-cliente';

INSERT INTO totali_cliente
SELECT
    cliente,
    COUNT(*)                              AS ordini,
    CAST(SUM(importo) AS DECIMAL(12, 2))  AS totale,
    MAX(ts)                               AS ultimo_ordine
FROM ordini
GROUP BY cliente;
