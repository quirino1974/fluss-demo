import os

SECRET_KEY = os.environ["SUPERSET_SECRET_KEY"]

# Metadati di Superset (utenti, grafici, dashboard) in ./data/superset
SQLALCHEMY_DATABASE_URI = "sqlite:////app/superset_home/superset.db?check_same_thread=false"

# Niente BABEL_DEFAULT_LOCALE = "it": la pagina di login non riesce a scaricare
# il pacchetto lingua senza autenticazione e resta nera.
