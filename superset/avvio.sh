#!/usr/bin/env bash
# Inizializza Superset (idempotente) e avvia il web server
set -e

superset db upgrade
superset fab create-admin --username admin --password admin \
    --firstname Admin --lastname Fluss --email admin@localhost || true
superset init

# Connessione al PostgreSQL in cui Flink copia i dati di Fluss
superset set-database-uri -d "Fluss (PostgreSQL)" \
    -u "postgresql+psycopg2://fluss:fluss@postgres:5432/fluss"

exec /usr/bin/run-server.sh
