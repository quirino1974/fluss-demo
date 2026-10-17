#!/usr/bin/env python3
"""Gestione dei job di streaming Flink dello stack Fluss.

Ogni file .sql in questa cartella è un job: gli statement vengono eseguiti
in ordine in una sessione del Flink SQL Gateway; il nome del job è il nome
del file (deve coincidere con 'pipeline.name' nel file).

Uso:
  flink_jobs.py start [nome ...]   avvia i job non già in esecuzione (default: tutti)
  flink_jobs.py stop  [nome ...]   ferma i job (default: tutti)
  flink_jobs.py status             mostra i job Flink e il loro stato
"""

import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

GATEWAY = "http://localhost:8084"
FLINK = "http://localhost:8083"
JOBS_DIR = Path(__file__).resolve().parent


def call(method, url, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, method=method, data=data, headers={"content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            text = r.read().decode()
            return json.loads(text) if text else {}
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{method} {url} -> HTTP {e.code}: {e.read().decode()[:2000]}") from None


def job_files(names):
    files = {f.stem: f for f in sorted(JOBS_DIR.glob("*.sql"))}
    unknown = [n for n in names if n not in files]
    if unknown:
        sys.exit(f"Job sconosciuti: {', '.join(unknown)} (disponibili: {', '.join(files)})")
    return {n: files[n] for n in (names or files)}


def statements(path):
    lines = [l for l in path.read_text().splitlines() if not l.strip().startswith("--")]
    return [s.strip() for s in "\n".join(lines).split(";") if s.strip()]


def running_jobs():
    jobs = call("GET", f"{FLINK}/jobs/overview")["jobs"]
    return {j["name"]: j["jid"] for j in jobs if j["state"] in ("RUNNING", "CREATED", "INITIALIZING", "RESTARTING")}


def run_statement(session, sql):
    op = call("POST", f"{GATEWAY}/v2/sessions/{session}/statements", {"statement": sql})["operationHandle"]
    uri = f"/v2/sessions/{session}/operations/{op}/result/0?rowFormat=JSON"
    for _ in range(120):
        res = call("GET", GATEWAY + uri)
        if res["resultType"] == "EOS":
            return
        uri = res["nextResultUri"]
        time.sleep(1)
    raise RuntimeError(f"Timeout in attesa del risultato di: {sql[:80]}")


def start(names):
    running = running_jobs()
    for name, path in job_files(names).items():
        if name in running:
            print(f"[OK] {name} già in esecuzione ({running[name][:8]})")
            continue
        for attempt in range(1, 7):
            session = call("POST", f"{GATEWAY}/v2/sessions", {"sessionName": name})["sessionHandle"]
            try:
                for sql in statements(path):
                    run_statement(session, sql)
                break
            except RuntimeError as e:
                # Subito dopo l'avvio Fluss può non essere ancora pronto
                if attempt == 6:
                    raise
                print(f"[WAIT] {name}: tentativo {attempt} fallito, riprovo tra 10 s ({str(e)[:120]})")
                time.sleep(10)
            finally:
                call("DELETE", f"{GATEWAY}/v2/sessions/{session}")
        print(f"[OK] {name} avviato")


def stop(names):
    running = running_jobs()
    for name in job_files(names):
        if name not in running:
            print(f"[INFO] {name} non è in esecuzione")
            continue
        call("PATCH", f"{FLINK}/jobs/{running[name]}?mode=cancel")
        print(f"[OK] {name} fermato")


def status():
    for j in sorted(call("GET", f"{FLINK}/jobs/overview")["jobs"], key=lambda j: j["start-time"]):
        started = time.strftime("%d/%m %H:%M:%S", time.localtime(j["start-time"] / 1000))
        print(f"{j['state']:<10} {started}  {j['name'][:70]}")


if __name__ == "__main__":
    cmd, args = (sys.argv[1], sys.argv[2:]) if len(sys.argv) > 1 else ("status", [])
    if cmd == "start":
        start(args)
    elif cmd == "stop":
        stop(args)
    elif cmd == "status":
        status()
    else:
        sys.exit(__doc__)
