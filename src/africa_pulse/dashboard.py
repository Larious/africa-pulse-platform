"""Local read-only dashboard for reviewing live Africa Pulse warehouse results."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from africa_pulse.settings import Settings
from africa_pulse.warehouse.client import get_client

PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Africa Pulse | Operations</title>
  <style>
    :root { --ink:#102a43; --muted:#627d98; --line:#d9e2ec; --paper:#f8fbfd; --blue:#0b6e99; --green:#138a72; --amber:#b45309; --red:#b42318; }
    * { box-sizing:border-box; } body { margin:0; font-family:Inter, ui-sans-serif, system-ui, sans-serif; background:var(--paper); color:var(--ink); }
    header { background:#102a43; color:white; padding:26px max(24px, calc((100vw - 1160px)/2)); }
    h1 { margin:0; font-size:26px; letter-spacing:0; } header p { margin:5px 0 0; color:#cbd8e6; font-size:14px; }
    main { max-width:1160px; margin:0 auto; padding:24px; } .meta { display:flex; justify-content:space-between; gap:16px; align-items:center; margin-bottom:20px; color:var(--muted); font-size:13px; }
    .status { color:var(--green); font-weight:700; } .grid { display:grid; grid-template-columns:repeat(3, minmax(0,1fr)); gap:16px; }
    section { margin-top:28px; } h2 { font-size:16px; margin:0 0 10px; } .tile { border:1px solid var(--line); border-radius:6px; background:white; padding:18px; min-height:145px; }
    .city { font-weight:700; font-size:17px; } .metric { font-size:28px; font-weight:750; margin:16px 0 4px; } .label { font-size:12px; color:var(--muted); }
    .bar { height:7px; background:#e8eff5; margin-top:12px; } .bar i { display:block; height:100%; background:var(--blue); } table { width:100%; border-collapse:collapse; background:white; border:1px solid var(--line); border-radius:6px; overflow:hidden; font-size:13px; }
    th { text-align:left; padding:11px 12px; background:#edf3f8; color:#486581; font-weight:700; } td { padding:11px 12px; border-top:1px solid var(--line); } .pill { display:inline-block; padding:3px 7px; border-radius:4px; font-weight:700; font-size:12px; background:#e5f5ef; color:#08725c; }
    .pill.failed { background:#fee4e2; color:var(--red); } .empty { padding:24px; color:var(--muted); background:white; border:1px solid var(--line); }
    @media (max-width:720px) { .grid { grid-template-columns:1fr; } main { padding:16px; } .meta { align-items:flex-start; flex-direction:column; } th:nth-child(4), td:nth-child(4) { display:none; } }
  </style>
</head>
<body>
  <header><h1>Africa Pulse</h1><p>Live warehouse operations for Lagos, Abuja, and Cape Town</p></header>
  <main>
    <div class="meta"><span id="updated">Loading warehouse data...</span><span id="health" class="status">Checking source freshness</span></div>
    <section><h2>Daily Mobility</h2><div id="cities" class="grid"></div></section>
    <section><h2>City Intelligence Score Coverage</h2><div id="scores" class="grid"></div></section>
    <section><h2>Recent Source Runs</h2><div id="runs"></div></section>
    <section><h2>Source Freshness</h2><div id="freshness"></div></section>
  </main>
  <script>
    const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    const cityName = id => ({lagos_ng:'Lagos', abuja_ng:'Abuja', cape_town_za:'Cape Town'}[id] || id);
    const number = (value, decimals=1) => value == null ? 'Unavailable' : Number(value).toFixed(decimals);
    function table(rows, columns) {
      if (!rows.length) return '<div class="empty">No warehouse records yet. Run a collection workflow, then refresh the dashboard.</div>';
      return '<table><thead><tr>' + columns.map(c => `<th>${escape(c.label)}</th>`).join('') + '</tr></thead><tbody>' + rows.map(row => '<tr>' + columns.map(c => `<td>${c.render ? c.render(row[c.key]) : escape(row[c.key])}</td>`).join('') + '</tr>').join('') + '</tbody></table>';
    }
    async function load() {
      const response = await fetch('/api/summary');
      const data = await response.json();
      if (data.error) throw new Error(data.error);
      document.querySelector('#updated').textContent = `Updated ${new Date(data.generated_at).toLocaleString()}`;
      const stale = data.freshness.some(row => row.is_stale);
      const health = document.querySelector('#health');
      health.textContent = stale ? 'Stale source data present' : 'All monitored sources within freshness threshold';
      health.style.color = stale ? 'var(--red)' : 'var(--green)';
      document.querySelector('#cities').innerHTML = data.mobility.map(row => `<article class="tile"><div class="city">${cityName(row.city_id)}</div><div class="metric">${number(100 * row.median_congestion_ratio)}%</div><div class="label">Median congestion ratio</div><div class="bar"><i style="width:${Math.min(100, Math.max(0, row.valid_sample_coverage_pct))}%"></i></div><div class="label">${number(row.valid_sample_coverage_pct, 0)}% validated road-sample coverage</div></article>`).join('') || '<div class="empty">No mobility mart records yet.</div>';
      document.querySelector('#scores').innerHTML = data.scores.map(row => `<article class="tile"><div class="city">${cityName(row.city_id)}</div><div class="metric">${escape(row.score_status)}</div><div class="label">Score status</div><div class="bar"><i style="width:${Math.min(100, Math.max(0, row.weighted_coverage_pct))}%"></i></div><div class="label">${number(row.weighted_coverage_pct, 0)}% weighted component coverage</div></article>`).join('') || '<div class="empty">No score mart records yet.</div>';
      document.querySelector('#runs').innerHTML = table(data.runs, [{key:'source_id',label:'Source'}, {key:'status',label:'Status',render:v=>`<span class="pill ${v === 'failed' ? 'failed' : ''}">${escape(v)}</span>`}, {key:'records_received',label:'Received'}, {key:'records_inserted',label:'Inserted'}, {key:'started_at',label:'Started'}]);
      document.querySelector('#freshness').innerHTML = table(data.freshness, [{key:'domain',label:'Domain'}, {key:'freshest_observation_at',label:'Latest observation'}, {key:'age_minutes',label:'Age (minutes)'}, {key:'is_stale',label:'Status',render:v=>`<span class="pill ${v ? 'failed' : ''}">${v ? 'stale' : 'current'}</span>`}]);
    }
    load().catch(error => { document.querySelector('#updated').textContent = `Dashboard error: ${error.message}`; });
    setInterval(() => load().catch(() => {}), 60000);
  </script>
</body>
</html>"""


def named_rows(client, query):
    return list(client.query(query).named_results())


def dashboard_summary(client):
    freshness = named_rows(client, "SELECT 'traffic' AS domain, max(observed_at) AS freshest_observation_at, dateDiff('minute', freshest_observation_at, now()) AS age_minutes, age_minutes > 180 AS is_stale FROM warehouse.fact_traffic_flow_observation FINAL UNION ALL SELECT 'weather', max(observed_at), dateDiff('minute', max(observed_at), now()), dateDiff('minute', max(observed_at), now()) > 180 FROM warehouse.fact_weather_observation FINAL UNION ALL SELECT 'air_quality', max(observed_at), dateDiff('minute', max(observed_at), now()), dateDiff('minute', max(observed_at), now()) > 180 FROM warehouse.fact_air_quality_observation FINAL UNION ALL SELECT 'fx', max(observed_at), dateDiff('minute', max(observed_at), now()), dateDiff('minute', max(observed_at), now()) > 180 FROM warehouse.fact_fx_rate FINAL UNION ALL SELECT 'commercial', max(commercial.snapshot_at), dateDiff('minute', max(commercial.snapshot_at), now()), dateDiff('minute', max(commercial.snapshot_at), now()) > 11520 OR (SELECT argMax(status, started_at) FROM control.ingestion_run FINAL WHERE source_id = 'openstreetmap_overpass_commercial_v1') != 'completed' FROM warehouse.fact_commercial_poi_snapshot AS commercial FINAL INNER JOIN control.ingestion_run AS run FINAL ON commercial.run_id = run.run_id WHERE run.status = 'completed'")
    return {
        "mobility": named_rows(client, "SELECT * FROM mart.city_mobility_daily FINAL ORDER BY local_date DESC, city_id LIMIT 3"),
        "scores": named_rows(client, "SELECT * FROM mart.city_intelligence_daily FINAL ORDER BY local_date DESC, city_id LIMIT 3"),
        "runs": named_rows(client, "SELECT source_id, status, records_received, records_inserted, started_at FROM control.ingestion_run FINAL ORDER BY started_at DESC LIMIT 10"),
        "freshness": freshness,
    }


class DashboardHandler(BaseHTTPRequestHandler):
    def do_HEAD(self):
        if self.path == "/":
            self.respond(200, "text/html; charset=utf-8", b"")
            return
        if self.path == "/api/summary":
            self.respond(200, "application/json", b"")
            return
        self.respond(404, "text/plain; charset=utf-8", b"")

    def do_GET(self):
        if self.path == "/":
            self.respond(200, "text/html; charset=utf-8", PAGE.encode())
            return
        if self.path == "/api/summary":
            try:
                payload = dashboard_summary(self.server.client) | {"generated_at": self.date_time_string()}
                self.respond(200, "application/json", json.dumps(payload, default=str).encode())
            except Exception as error:  # noqa: BLE001 - return a readable error at the HTTP boundary.
                self.respond(500, "application/json", json.dumps({"error": str(error)}).encode())
            return
        self.respond(404, "text/plain; charset=utf-8", b"Not found")

    def respond(self, status, content_type, body):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, _format, *_args):
        return


def run(host="127.0.0.1", port=8765):
    server = ThreadingHTTPServer((host, port), DashboardHandler)
    server.client = get_client(Settings.from_environment())
    print(f"Africa Pulse dashboard: http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
