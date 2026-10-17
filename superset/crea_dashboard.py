#!/usr/bin/env python3
"""Crea in Superset la dashboard "Ordini Fluss in tempo reale" via API.

Usa la connessione "Fluss (PostgreSQL)" (creata da avvio.sh) e le tabelle
ordini e totali_cliente che i job Flink export-postgres-* tengono aggiornate.
Se la dashboard esiste già non fa nulla: per ricrearla cancellala da Superset.
"""

import http.cookiejar
import json
import urllib.error
import urllib.parse
import urllib.request

SUPERSET = "http://localhost:8088"
USER, PASSWORD = "admin", "admin"
DB_NAME = "Fluss (PostgreSQL)"
SLUG = "ordini-fluss"
REFRESH_SECONDS = 10

opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
headers = {"content-type": "application/json"}


def api(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(SUPERSET + path, method=method, data=data, headers=headers)
    try:
        with opener.open(req, timeout=60) as r:
            return json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{method} {path} -> HTTP {e.code}: {e.read().decode()[:1500]}") from None


def rison_filter(col, value):
    return "?q=" + urllib.parse.quote(f"(filters:!((col:{col},opr:eq,value:'{value}')))")


def login():
    token = api("POST", "/api/v1/security/login",
                {"username": USER, "password": PASSWORD, "provider": "db", "refresh": True})["access_token"]
    headers["Authorization"] = f"Bearer {token}"
    headers["X-CSRFToken"] = api("GET", "/api/v1/security/csrf_token/")["result"]
    headers["Referer"] = SUPERSET


def dataset(db_id, table):
    found = api("GET", "/api/v1/dataset/" + rison_filter("table_name", table))["result"]
    if found:
        return found[0]["id"]
    return api("POST", "/api/v1/dataset/", {"database": db_id, "schema": "public", "table_name": table})["id"]


def sql_metric(expr, label):
    return {"expressionType": "SQL", "sqlExpression": expr, "label": label}


def chart(name, viz_type, ds_id, params):
    params = {"viz_type": viz_type, "datasource": f"{ds_id}__table", "adhoc_filters": [], **params}
    return api("POST", "/api/v1/chart/", {
        "slice_name": name, "viz_type": viz_type, "datasource_id": ds_id,
        "datasource_type": "table", "params": json.dumps(params),
    })["id"]


def layout(rows):
    pos = {
        "DASHBOARD_VERSION_KEY": "v2",
        "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
        "GRID_ID": {"type": "GRID", "id": "GRID_ID", "children": [], "parents": ["ROOT_ID"]},
    }
    for r, row in enumerate(rows):
        row_id = f"ROW-{r}"
        pos["GRID_ID"]["children"].append(row_id)
        pos[row_id] = {"type": "ROW", "id": row_id, "children": [], "parents": ["ROOT_ID", "GRID_ID"],
                       "meta": {"background": "BACKGROUND_TRANSPARENT"}}
        for chart_id, name, width, height in row:
            cid = f"CHART-{chart_id}"
            pos[row_id]["children"].append(cid)
            pos[cid] = {"type": "CHART", "id": cid, "children": [], "parents": ["ROOT_ID", "GRID_ID", row_id],
                        "meta": {"width": width, "height": height, "chartId": chart_id, "sliceName": name}}
    return pos


def main():
    login()
    if api("GET", "/api/v1/dashboard/" + rison_filter("slug", SLUG))["result"]:
        print(f"[OK] La dashboard esiste già: {SUPERSET}/superset/dashboard/{SLUG}/")
        return

    dbs = api("GET", "/api/v1/database/" + rison_filter("database_name", DB_NAME))["result"]
    if not dbs:
        raise SystemExit(f"Connessione '{DB_NAME}' non trovata: controlla i log del container superset")
    db_id = dbs[0]["id"]
    ordini = dataset(db_id, "ordini")
    totali = dataset(db_id, "totali_cliente")

    n_ordini = "Ordini totali"
    c_ordini = chart(n_ordini, "big_number_total", ordini, {
        "metric": sql_metric("COUNT(*)", "Ordini"), "y_axis_format": ",d", "subheader": "ordini in Fluss"})
    n_incasso = "Incasso totale"
    c_incasso = chart(n_incasso, "big_number_total", ordini, {
        "metric": sql_metric("SUM(importo)", "Incasso"), "y_axis_format": ",.2f", "subheader": "euro"})
    n_medio = "Importo medio"
    c_medio = chart(n_medio, "big_number_total", ordini, {
        "metric": sql_metric("AVG(importo)", "Medio"), "y_axis_format": ",.2f", "subheader": "euro per ordine"})
    n_barre = "Totale per cliente (calcolato da Flink)"
    c_barre = chart(n_barre, "echarts_timeseries_bar", totali, {
        "x_axis": "cliente", "metrics": [sql_metric("SUM(totale)", "Totale")], "groupby": [],
        "x_axis_sort": "Totale", "x_axis_sort_asc": False, "row_limit": 100,
        "y_axis_format": ",.2f", "show_legend": False, "show_value": True})
    n_linea = "Ordini al minuto per cliente"
    c_linea = chart(n_linea, "echarts_timeseries_line", ordini, {
        "x_axis": "ts", "time_grain_sqla": "PT1M", "metrics": [sql_metric("COUNT(*)", "Ordini")],
        "groupby": ["cliente"], "row_limit": 10000, "rich_tooltip": True, "time_range": "No filter"})
    n_tabella = "Totali per cliente"
    c_tabella = chart(n_tabella, "table", totali, {
        "query_mode": "raw", "all_columns": ["cliente", "ordini", "totale", "ultimo_ordine"],
        "order_by_cols": [json.dumps(["totale", False])], "row_limit": 100})
    n_ultimi = "Ultimi ordini"
    c_ultimi = chart(n_ultimi, "table", ordini, {
        "query_mode": "raw", "all_columns": ["ts", "id_ordine", "cliente", "importo"],
        "order_by_cols": [json.dumps(["ts", False])], "row_limit": 20})

    rows = [
        [(c_ordini, n_ordini, 4, 30), (c_incasso, n_incasso, 4, 30), (c_medio, n_medio, 4, 30)],
        [(c_barre, n_barre, 6, 50), (c_linea, n_linea, 6, 50)],
        [(c_tabella, n_tabella, 6, 50), (c_ultimi, n_ultimi, 6, 50)],
    ]
    dash = api("POST", "/api/v1/dashboard/", {
        "dashboard_title": "Ordini Fluss in tempo reale",
        "slug": SLUG,
        "published": True,
        "position_json": json.dumps(layout(rows)),
        "json_metadata": json.dumps({"refresh_frequency": REFRESH_SECONDS, "timed_refresh_immune_slices": []}),
    })["id"]
    for row in rows:
        for chart_id, *_ in row:
            api("PUT", f"/api/v1/chart/{chart_id}", {"dashboards": [dash]})
    print(f"[OK] Dashboard creata: {SUPERSET}/superset/dashboard/{SLUG}/")


if __name__ == "__main__":
    main()
