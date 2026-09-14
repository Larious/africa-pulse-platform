"""Clearly labelled synthetic scenario for demonstrating missing analytical capabilities."""

import argparse
import json
import random
from datetime import UTC, date, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from africa_pulse.settings import Settings
from africa_pulse.warehouse.client import get_client, insert_rows

SCENARIO_ID = "synthetic_capstone_demo_v1"
SEED = 20260914
SCHEMA = """
CREATE DATABASE IF NOT EXISTS synthetic_demo;
CREATE TABLE IF NOT EXISTS synthetic_demo.city_daily_scenario
(
    scenario_id LowCardinality(String), seed UInt64, city_id LowCardinality(String), city_name String,
    local_date Date, congestion_ratio Float32, rainfall_mm Float32, pm2_5 Float32,
    nitrogen_dioxide Float32, usd_rate Float64, fuel_local_per_litre Float64,
    fuel_usd_per_litre Float64, population UInt64, commercial_services UInt32,
    commercial_services_per_100k Float32, city_intelligence_score Float32,
    trend_status LowCardinality(String), generated_at DateTime64(3, 'UTC')
)
ENGINE = ReplacingMergeTree(generated_at)
PARTITION BY toYYYYMM(local_date)
ORDER BY (scenario_id, city_id, local_date);
"""

CITIES = {
    "lagos_ng": {"name": "Lagos", "population": 15500000, "usd_rate": 1550.0, "fuel": 940.0, "congestion": 0.48, "rain": 8.0, "pm": 29.0, "no2": 31.0, "services": 32500, "trend": -0.002},
    "abuja_ng": {"name": "Abuja", "population": 4100000, "usd_rate": 1550.0, "fuel": 920.0, "congestion": 0.33, "rain": 5.5, "pm": 20.0, "no2": 18.0, "services": 10800, "trend": -0.001},
    "cape_town_za": {"name": "Cape Town", "population": 4800000, "usd_rate": 18.2, "fuel": 24.0, "congestion": 0.27, "rain": 3.0, "pm": 15.0, "no2": 14.0, "services": 17100, "trend": 0.0005},
}


def create_schema(client) -> None:
    for statement in SCHEMA.split(";"):
        if statement.strip():
            client.command(statement)


def scenario_rows(start_date: date = date(2026, 8, 11), days: int = 35) -> list[dict]:
    """Return a repeatable illustrative scenario; these are not source observations."""
    generator = random.Random(SEED)
    generated_at = datetime.now(UTC)
    rows = []
    for city_id, baseline in CITIES.items():
        services_per_100k = baseline["services"] / baseline["population"] * 100000
        for day_index in range(days):
            local_date = start_date + timedelta(days=day_index)
            rainfall = max(0, baseline["rain"] + generator.gauss(0, 2.3))
            congestion = min(0.9, max(0.05, baseline["congestion"] + baseline["trend"] * day_index + rainfall * 0.004 + generator.gauss(0, 0.018)))
            pm2_5 = max(3, baseline["pm"] + congestion * 9 + generator.gauss(0, 2.0))
            no2 = max(2, baseline["no2"] + congestion * 7 + generator.gauss(0, 1.5))
            usd_rate = baseline["usd_rate"] * (1 + 0.0008 * day_index + generator.gauss(0, 0.003))
            fuel_local = baseline["fuel"] * (1 + 0.0015 * day_index + generator.gauss(0, 0.006))
            fuel_usd = fuel_local / usd_rate
            score = max(0, min(100, 100 - congestion * 55 - pm2_5 * 0.8 + services_per_100k * 0.06 - fuel_usd * 2))
            trend_status = "improving" if baseline["trend"] < 0 else "deteriorating"
            rows.append({
                "scenario_id": SCENARIO_ID, "seed": SEED, "city_id": city_id, "city_name": baseline["name"],
                "local_date": local_date, "congestion_ratio": congestion, "rainfall_mm": rainfall, "pm2_5": pm2_5,
                "nitrogen_dioxide": no2, "usd_rate": usd_rate, "fuel_local_per_litre": fuel_local,
                "fuel_usd_per_litre": fuel_usd, "population": baseline["population"], "commercial_services": baseline["services"],
                "commercial_services_per_100k": services_per_100k, "city_intelligence_score": score,
                "trend_status": trend_status, "generated_at": generated_at,
            })
    return rows


def generate(client) -> int:
    create_schema(client)
    return insert_rows(client, "synthetic_demo.city_daily_scenario", scenario_rows())


def query_rows(client, sql: str, parameters: dict | None = None) -> list[dict]:
    return list(client.query(sql, parameters=parameters).named_results())


def summary(client) -> dict:
    latest = query_rows(client, "SELECT * FROM synthetic_demo.city_daily_scenario FINAL WHERE scenario_id = {scenario_id:String} ORDER BY local_date DESC LIMIT 1 BY city_id", {"scenario_id": SCENARIO_ID})
    answers = query_rows(client, "SELECT city_name, round(avg(congestion_ratio), 3) AS avg_congestion_ratio, round(corr(rainfall_mm, congestion_ratio), 3) AS rainfall_congestion_correlation, round(avg(pm2_5), 1) AS avg_pm2_5, round(avg(fuel_usd_per_litre), 2) AS avg_fuel_usd_per_litre, any(commercial_services_per_100k) AS services_per_100k, round(avg(city_intelligence_score), 1) AS average_score, any(trend_status) AS trend_status FROM synthetic_demo.city_daily_scenario FINAL WHERE scenario_id = {scenario_id:String} GROUP BY city_name ORDER BY average_score DESC", {"scenario_id": SCENARIO_ID})
    return {"scenario_id": SCENARIO_ID, "seed": SEED, "label": "SYNTHETIC DEMONSTRATION ONLY - NOT REAL CITY DATA", "latest": latest, "answers": answers}


PAGE = """<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'><title>Africa Pulse | Synthetic Demonstration</title><style>:root{--ink:#102a43;--muted:#627d98;--line:#d9e2ec;--paper:#f8fbfd;--red:#b42318;--blue:#0b6e99}*{box-sizing:border-box}body{margin:0;font-family:Inter,system-ui,sans-serif;background:var(--paper);color:var(--ink)}header{background:#102a43;color:white;padding:24px max(24px,calc((100vw - 1160px)/2))}h1{margin:0;font-size:26px}header p{margin:6px 0 0;color:#cbd8e6}main{max-width:1160px;margin:auto;padding:24px}.warning{background:#fee4e2;border:1px solid #fecdca;color:#8a1c13;padding:14px;font-weight:750}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin-top:18px}.tile,table{background:white;border:1px solid var(--line);border-radius:6px}.tile{padding:18px}.city{font-size:18px;font-weight:750}.metric{font-size:27px;font-weight:750;margin:14px 0 3px}.label{font-size:12px;color:var(--muted)}section{margin-top:28px}h2{font-size:17px}table{width:100%;border-collapse:collapse;font-size:13px}th,td{text-align:left;padding:11px;border-bottom:1px solid var(--line)}th{background:#edf3f8;color:#486581}@media(max-width:720px){.grid{grid-template-columns:1fr}th:nth-child(3),td:nth-child(3){display:none}}</style></head><body><header><h1>Africa Pulse: Synthetic Scenario</h1><p>Separate capability demonstration for Lagos, Abuja, and Cape Town</p></header><main><div class='warning'>SYNTHETIC DEMONSTRATION ONLY. Values are deterministic simulated inputs for testing analytical logic. They are not observations, forecasts, or claims about any city.</div><section><h2>Latest simulated city measures</h2><div id='cards' class='grid'></div></section><section><h2>Question-supporting simulated outputs: 35-day scenario</h2><table><thead><tr><th>City</th><th>Congestion</th><th>Rainfall relationship</th><th>PM2.5</th><th>Fuel USD/L</th><th>Services / 100k</th><th>Score</th><th>Trend</th></tr></thead><tbody id='answers'></tbody></table></section></main><script>const n=(v,d=1)=>Number(v).toFixed(d);async function load(){const d=await (await fetch('/api/summary')).json();document.querySelector('#cards').innerHTML=d.latest.map(r=>`<article class='tile'><div class='city'>${r.city_name}</div><div class='metric'>${n(r.city_intelligence_score)}</div><div class='label'>Synthetic City Intelligence Score</div><div class='label'>${n(100*r.congestion_ratio)}% congestion | ${n(r.rainfall_mm)} mm rainfall</div></article>`).join('');document.querySelector('#answers').innerHTML=d.answers.map(r=>`<tr><td>${r.city_name}</td><td>${n(100*r.avg_congestion_ratio)}%</td><td>${n(r.rainfall_congestion_correlation,2)} correlation</td><td>${n(r.avg_pm2_5)} ug/m3</td><td>$${n(r.avg_fuel_usd_per_litre,2)}</td><td>${n(r.services_per_100k)}</td><td>${n(r.average_score)}</td><td>${r.trend_status}</td></tr>`).join('')}load().catch(console.error)</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.respond(200, "text/html; charset=utf-8", PAGE.encode())
        elif self.path == "/api/summary":
            self.respond(200, "application/json", json.dumps(summary(self.server.client), default=str).encode())
        else:
            self.respond(404, "text/plain; charset=utf-8", b"Not found")

    def respond(self, status, content_type, body):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, _format, *_args):
        return


def run_dashboard(port: int = 8766) -> None:
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.client = get_client(Settings.from_environment())
    print(f"Synthetic dashboard: http://127.0.0.1:{port}")
    server.serve_forever()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the isolated Africa Pulse synthetic demonstration.")
    parser.add_argument("--generate", action="store_true", help="Generate the deterministic synthetic scenario.")
    parser.add_argument("--dashboard", action="store_true", help="Serve the synthetic dashboard on port 8766.")
    args = parser.parse_args()
    client = get_client(Settings.from_environment())
    if args.generate:
        print(f"Inserted {generate(client)} synthetic scenario rows into synthetic_demo.")
    if args.dashboard:
        run_dashboard()
    if not args.generate and not args.dashboard:
        parser.error("choose --generate, --dashboard, or both")


if __name__ == "__main__":
    main()
