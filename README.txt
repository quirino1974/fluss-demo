FLUSS DEMO
Cruscotti in tempo reale con Apache Fluss, Apache Flink, PostgreSQL e Apache Superset.

Flink genera un ordine al secondo e lo scrive in Fluss, calcola in streaming i totali
per cliente, copia ordini e totali in PostgreSQL; Superset li mostra in una dashboard
che si aggiorna ogni 10 secondi. n8n contiene un flusso di prova che inserisce ordini
e legge i totali tramite il Flink SQL Gateway.

Autore: Quirino Scaramastra

Prima di installare leggere PREREQUISITES.txt. Le modifiche tra una versione e l'altra
sono in RELEASE-NOTES.txt.


INSTALLAZIONE

  git clone https://github.com/quirino1974/fluss-demo.git
  cd fluss-demo
  chmod +x start.sh stop.sh


AVVIO

  ./start.sh

Lo script:
1. genera il file .env con la chiave segreta di Superset (solo la prima volta);
2. crea le cartelle dei dati in ./data;
3. costruisce le immagini di Flink e Superset e avvia tutti i container;
4. aspetta che Flink, SQL Gateway, Superset e n8n rispondano;
5. avvia i job di streaming Flink della cartella jobs/;
6. crea la dashboard di Superset e importa il flusso in n8n, se non ci sono già.

Il primo avvio scarica e costruisce le immagini: 5-10 minuti, secondo la connessione.
I successivi circa un minuto.


INDIRIZZI

  Superset    http://localhost:8088/superset/dashboard/ordini-fluss/   admin / admin
  Flink UI    http://localhost:8083
  SQL Gateway http://localhost:8084
  n8n         http://localhost:5678
  RustFS      http://localhost:9001                                    rustfsadmin / rustfsadmin
  PostgreSQL  localhost:5433, database fluss                           fluss / fluss

Sono credenziali di laboratorio: non esporre queste porte fuori dal proprio PC.

Al primo accesso n8n chiede di creare l'utente proprietario. Il flusso si chiama
"Demo Fluss - ordini via Flink SQL Gateway": aprirlo e premere Execute workflow.


ARRESTO

  ./stop.sh

I dati restano in ./data e vengono ritrovati al successivo ./start.sh.


RIPARTIRE DA ZERO

  ./stop.sh
  sudo rm -rf data .env
  ./start.sh

sudo serve perché alcuni file in data/ appartengono agli utenti dei container.


JOB FLINK

  python3 jobs/flink_jobs.py status                    elenco dei job e stato
  python3 jobs/flink_jobs.py start [nome]              avvia i job non attivi
  python3 jobs/flink_jobs.py stop [nome]               ferma i job

  generatore-ordini        un ordine casuale al secondo nella tabella Fluss ordini
  totali-per-cliente       aggiorna in streaming la tabella Fluss totali_cliente
  export-postgres-ordini   copia ordini in PostgreSQL
  export-postgres-totali   copia totali_cliente in PostgreSQL

Il generatore produce circa 3.600 ordini all'ora: se il lab resta acceso a lungo,
fermarlo con  python3 jobs/flink_jobs.py stop generatore-ordini

Ogni file .sql in jobs/ è un job: per aggiungerne uno basta un nuovo file con
SET 'pipeline.name' = '<nome-del-file>'; prima della INSERT.


INTERROGARE I DATI

Flink SQL client sulle tabelle Fluss:

  docker compose run --rm sql-client

  CREATE CATALOG fluss_catalog WITH ('type' = 'fluss', 'bootstrap.servers' = 'coordinator-server:9123');
  USE CATALOG fluss_catalog;
  SET 'sql-client.execution.result-mode' = 'tableau';
  SET 'execution.runtime-mode' = 'batch';
  SELECT * FROM totali_cliente LIMIT 10;

PostgreSQL:

  docker compose exec postgres psql -U fluss -d fluss -c "SELECT * FROM totali_cliente ORDER BY totale DESC"


LICENZA

Apache License 2.0, vedi il file LICENSE.
n8n è distribuito con la Sustainable Use License (fair-code) ed è usato solo per
laboratorio e prototipazione.
