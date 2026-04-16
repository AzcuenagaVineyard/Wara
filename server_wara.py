#!/usr/bin/env python3
"""
WARA Local API Server — python3 server_wara.py
Then open http://localhost:8765 in your browser.
"""
import sqlite3, json, sys
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler

DB_PATH   = Path(__file__).parent / "wara.db"
DASH_PATH = Path(__file__).parent / "dashboard.html"
PORT      = 8765

def query(sql, params=()):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args): pass

    def send_json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, path):
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        path   = self.path.split("?")[0]
        length = int(self.headers.get("Content-Length", 0))
        body   = self.rfile.read(length)
        try:
            data = json.loads(body)
        except Exception:
            self.send_json({"error": "Invalid JSON"}, 400)
            return
        if path == "/rastra_tag":
            fecha = data.get("fecha", "").strip()
            tag   = data.get("tag",   "").strip()
            if not fecha:
                self.send_json({"error": "fecha required"}, 400)
                return
            conn = sqlite3.connect(DB_PATH)
            if tag in ("rastra", "not_rastra"):
                conn.execute("INSERT OR REPLACE INTO rastra_tag (fecha, tag) VALUES (?,?)", (fecha, tag))
            else:
                conn.execute("DELETE FROM rastra_tag WHERE fecha=?", (fecha,))
            conn.commit()
            conn.close()
            self.send_json({"ok": True, "fecha": fecha, "tag": tag})
        else:
            self.send_json({"error": "Not found"}, 404)

    def do_GET(self):
        path = self.path.split("?")[0]

        if path in ("/", "/dashboard"):
            if DASH_PATH.exists():
                self.send_html(DASH_PATH)
            else:
                self.send_json({"error": "dashboard.html not found"}, 404)

        elif path == "/summary":
            self.send_json(query("SELECT * FROM daily_summary ORDER BY fecha"))

        elif path == "/stops":
            self.send_json(query("""
                SELECT d.*, s.dia_semana FROM detenciones d
                LEFT JOIN daily_summary s ON d.fecha = s.fecha
                ORDER BY d.fecha, d.hora
            """))

        elif path == "/sectors":
            self.send_json(query("""
                SELECT sector, COUNT(*) as n_paradas,
                    SUM(duracion_min) as total_min,
                    AVG(duracion_min) as avg_min,
                    MAX(duracion_min) as max_min
                FROM detenciones WHERE sector IS NOT NULL
                GROUP BY sector ORDER BY total_min DESC
            """))

        elif path == "/stats":
            rows = query("""
                SELECT COUNT(*) as dias, SUM(distancia_km) as total_km,
                    SUM(movimiento_min) as total_mov_min,
                    SUM(ralenti_min) as total_idle_min,
                    AVG(km_por_hora_mov) as avg_kmh,
                    MIN(fecha) as primer_dia, MAX(fecha) as ultimo_dia
                FROM daily_summary
            """)
            self.send_json(rows[0] if rows else {})

        elif path == "/health":
            self.send_json({"status": "ok", "db": str(DB_PATH), "exists": DB_PATH.exists()})

        elif path == "/rastra":
            rows = query("""
                SELECT d.fecha, d.dia_semana, d.distancia_km,
                    d.movimiento_min, d.ralenti_min,
                    d.vel_max_kmh, d.km_por_hora_mov,
                    d.hora_arranca, d.hora_termina,
                    COUNT(s.id) as total_stops,
                    SUM(CASE WHEN s.duracion_min <= 5 THEN 1 ELSE 0 END) as short_stops,
                    COALESCE(r.tag, '') as manual_tag
                FROM daily_summary d
                LEFT JOIN detenciones s ON d.fecha = s.fecha AND s.hora >= '06:00'
                LEFT JOIN rastra_tag r ON d.fecha = r.fecha
                GROUP BY d.fecha ORDER BY d.fecha
            """)
            result = []
            for row in rows:
                is_weekend = row["dia_semana"] in ("Sábado", "Domingo")
                dist_min   = 5.0 if is_weekend else 12.0
                stop_min   = 3   if is_weekend else 5
                auto       = (row["short_stops"] or 0) >= stop_min and (row["distancia_km"] or 0) >= dist_min
                tag        = row["manual_tag"]
                row["auto_detected"] = auto
                row["is_rastra"]     = (tag == "rastra") or (auto and tag != "not_rastra")
                result.append(row)
            self.send_json(result)

        elif path == "/rastra_stops":
            self.send_json(query("""
                SELECT d.sector, SUM(d.duracion_min) as total_min, COUNT(*) as n_stops
                FROM detenciones d
                WHERE d.sector IS NOT NULL AND d.hora >= '06:00'
                AND d.fecha IN (
                    SELECT ds.fecha FROM daily_summary ds
                    LEFT JOIN rastra_tag r ON ds.fecha = r.fecha
                    WHERE COALESCE(r.tag,'') = 'rastra'
                    OR (COALESCE(r.tag,'') != 'not_rastra'
                        AND CASE WHEN ds.dia_semana IN ('Sábado','Domingo')
                            THEN ds.distancia_km >= 5.0
                            ELSE ds.distancia_km >= 12.0 END)
                )
                GROUP BY d.sector ORDER BY total_min DESC
            """))

        else:
            self.send_json({"error": "Not found"}, 404)

def main():
    if not DB_PATH.exists():
        print(f"[!] Database not found: {DB_PATH}")
        print("    Run: python3 parse_wara.py pdfs/  first.")
        sys.exit(1)
    print(f"WARA Dashboard Server")
    print(f"  Database : {DB_PATH}")
    print(f"  Dashboard: http://localhost:{PORT}/")
    print(f"  Press Ctrl+C to stop\n")
    server = HTTPServer(("localhost", PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")

if __name__ == "__main__":
    main()
