-- Tabelle in cui i job Flink export-postgres-* copiano i dati di Fluss.
-- Eseguito solo alla prima creazione del database (cartella data/postgres vuota).

CREATE TABLE IF NOT EXISTS ordini (
    id_ordine  BIGINT PRIMARY KEY,
    cliente    TEXT,
    importo    NUMERIC(10, 2),
    ts         TIMESTAMP(3)
);

CREATE TABLE IF NOT EXISTS totali_cliente (
    cliente        TEXT PRIMARY KEY,
    ordini         BIGINT,
    totale         NUMERIC(12, 2),
    ultimo_ordine  TIMESTAMP(3)
);
