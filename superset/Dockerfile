# Superset 6.1.0 con il driver PostgreSQL (l'immagine ufficiale non lo include)
FROM apache/superset:6.1.0

USER root
RUN . /app/.venv/bin/activate && uv pip install --no-cache psycopg2-binary
USER superset
