#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

[ -f .env ] || echo "SUPERSET_SECRET_KEY=$(openssl rand -base64 42 | tr -d '\n')" > .env

mkdir -p data/rustfs data/zookeeper/data data/zookeeper/datalog data/tablet-server \
         data/postgres data/superset data/n8n
chmod a+rwx data/* data/zookeeper/* 2>/dev/null || true

docker compose up -d --build

wait_for() {
    local name="$1" url="$2" timeout="${3:-180}" elapsed=0
    printf "Attesa %s" "$name"
    until curl -sf -o /dev/null "$url"; do
        if [ "$elapsed" -ge "$timeout" ]; then
            echo " non risponde dopo ${timeout}s"
            return 1
        fi
        printf "."
        sleep 3
        elapsed=$((elapsed + 3))
    done
    echo " ok"
}

wait_for "Flink" "http://localhost:8083/overview"
wait_for "Flink SQL Gateway" "http://localhost:8084/v2/info"
wait_for "Superset" "http://localhost:8088/health"
wait_for "n8n" "http://localhost:5678/healthz"

python3 jobs/flink_jobs.py start
python3 superset/crea_dashboard.py

if ! docker compose exec -T n8n n8n list:workflow 2>/dev/null | grep -q '^demoFluss0000001|'; then
    docker compose exec -T n8n n8n import:workflow --input=/workflows/demo-fluss.json
fi

cat <<EOF

Superset   http://localhost:8088/superset/dashboard/ordini-fluss/  (admin / admin)
Flink      http://localhost:8083
n8n        http://localhost:5678
RustFS     http://localhost:9001  (rustfsadmin / rustfsadmin)
PostgreSQL localhost:5433  (fluss / fluss)
EOF
