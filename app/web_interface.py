"""Simple web interface for exposing latest analysis results."""

import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs

import structlog


class WebInterface:
    """Provides a minimal HTTP server for latest analysis data."""

    def __init__(self, port, config_path=None):
        self.logger = structlog.get_logger()
        self.port = port
        self.state = {'latest': None}
        self.config_path = config_path or os.getenv('CONFIG_PATH', 'config.yml')
        self.server = ThreadingHTTPServer(('0.0.0.0', port), self._handler())


    def _handler(self):
        state = self.state
        config_path = self.config_path
        port = self.port
        logger = self.logger

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path not in ('/', '/latest', '/health', '/config'):
                    self.send_response(404)
                    self.end_headers()
                    return

                if self.path == '/health':
                    self._send_json({'status': 'ok'})
                    return

                if self.path == '/latest':
                    self._send_json(state['latest'] or {'status': 'no_data'})
                    return

                if self.path == '/config':
                    self._send_json({'config': self._read_config()})
                    return

                self._send_html(self._render_page())

            def do_POST(self):
                if self.path != '/config':
                    self.send_response(404)
                    self.end_headers()
                    return

                length = int(self.headers.get('Content-Length', 0))
                payload = self.rfile.read(length).decode('utf-8')
                data = parse_qs(payload)
                config_body = data.get('config', [''])[0]

                if config_body:
                    self._write_config(config_body)
                    self._send_json({'status': 'saved'})
                else:
                    self._send_json({'status': 'empty'}, status=400)

            def log_message(self, format, *args):
                logger.info(format, *args)

            def _send_json(self, payload, status=200):
                body = json.dumps(payload, default=str).encode('utf-8')
                self.send_response(status)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _send_html(self, html):
                body = html.encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _read_config(self):
                try:
                    if os.path.isfile(config_path):
                        with open(config_path, 'r') as config_file:
                            return config_file.read()
                except Exception:
                    logger.exception('Failed reading config at %s', config_path)
                return ''

            def _write_config(self, config_body):
                try:
                    os.makedirs(os.path.dirname(config_path), exist_ok=True)
                    with open(config_path, 'w') as config_file:
                        config_file.write(config_body)
                except Exception:
                    logger.exception('Failed writing config at %s', config_path)

            def _render_page(self):
                latest_payload = json.dumps(state['latest'] or {'status': 'no_data'}, indent=2, default=str)
                config_body = self._read_config()
                return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>CryptoSignal Web Interface</title>
    <style>
      :root {{
        --bg: #0f172a;
        --card: #111827;
        --muted: #94a3b8;
        --accent: #38bdf8;
        --success: #22c55e;
        --danger: #f87171;
      }}
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0;
        font-family: "Inter", "Segoe UI", Arial, sans-serif;
        background: var(--bg);
        color: #e2e8f0;
      }}
      header {{
        padding: 24px 32px;
        border-bottom: 1px solid #1e293b;
        display: flex;
        justify-content: space-between;
        align-items: center;
      }}
      header h1 {{ margin: 0; font-size: 22px; }}
      header .meta {{ color: var(--muted); font-size: 13px; }}
      main {{ padding: 24px 32px 48px; }}
      .grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
        gap: 16px;
      }}
      .card {{
        background: var(--card);
        padding: 16px;
        border-radius: 12px;
        border: 1px solid #1e293b;
        box-shadow: 0 10px 20px rgba(15, 23, 42, 0.45);
      }}
      .card h2 {{ margin-top: 0; font-size: 18px; }}
      .pill {{
        display: inline-flex;
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 12px;
        background: #1f2937;
        color: var(--muted);
      }}
      .status-buy {{ color: var(--success); }}
      .status-sell {{ color: var(--danger); }}
      textarea {{
        width: 100%;
        min-height: 240px;
        border-radius: 8px;
        border: 1px solid #334155;
        background: #0b1220;
        color: #e2e8f0;
        padding: 12px;
        font-family: "Fira Code", monospace;
      }}
      pre {{
        background: #020617;
        color: #e2e8f0;
        padding: 12px;
        border-radius: 8px;
        overflow: auto;
      }}
      button {{
        background: var(--accent);
        color: #0f172a;
        border: none;
        padding: 10px 16px;
        border-radius: 8px;
        font-weight: 600;
        cursor: pointer;
      }}
      table {{ width: 100%; border-collapse: collapse; }}
      th, td {{ text-align: left; padding: 8px; border-bottom: 1px solid #1e293b; font-size: 13px; }}
      th {{ color: var(--muted); }}
    </style>
  </head>
  <body>
    <header>
      <div>
        <h1>CryptoSignal Control Center</h1>
        <div class="meta">Web interface running on port {port}</div>
      </div>
      <div class="pill">Live feed + config editor</div>
    </header>

    <main>
      <div class="grid">
        <div class="card" id="decision-card">
          <h2>Decision Snapshot</h2>
          <p class="meta">Latest decision signal across exchanges.</p>
          <div id="decision-content">Waiting for analysis...</div>
        </div>
        <div class="card">
          <h2>Latest Analysis (Raw)</h2>
          <pre id="latest-json">{latest_payload}</pre>
        </div>
      </div>

      <div class="grid" style="margin-top: 16px;">
        <div class="card">
          <h2>Config Editor</h2>
          <p class="meta">Persisted at <code>{config_path}</code>.</p>
          <form method="POST" action="/config">
            <textarea name="config">{config_body}</textarea>
            <br /><br />
            <button type="submit">Save Config</button>
          </form>
        </div>
        <div class="card">
          <h2>Decision Table</h2>
          <table>
            <thead>
              <tr>
                <th>Exchange</th>
                <th>Pair</th>
                <th>Signal</th>
                <th>Confidence</th>
                <th>Scenario</th>
                <th>Zone</th>
              </tr>
            </thead>
            <tbody id="decision-table">
              <tr><td colspan="6">Waiting for analysis...</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </main>

    <script>
      async function refreshData() {{
        try {{
          const response = await fetch('/latest');
          const data = await response.json();
          document.getElementById('latest-json').textContent = JSON.stringify(data, null, 2);

          const table = document.getElementById('decision-table');
          table.innerHTML = '';
          let snapshot = null;

          for (const exchange of Object.keys(data || {{}})) {{
            for (const pair of Object.keys(data[exchange] || {{}})) {{
              const decision = data[exchange][pair].decision;
              if (!decision || !decision.signal) {{
                continue;
              }}
              if (!snapshot) {{
                snapshot = {{ exchange, pair, decision }};
              }}
              const row = document.createElement('tr');
              row.innerHTML = `
                <td>${{exchange}}</td>
                <td>${{pair}}</td>
                <td class="${{decision.signal === 'buy' ? 'status-buy' : 'status-sell'}}">${{decision.signal}}</td>
                <td>${{decision.confidence || 0}}%</td>
                <td>${{decision.scenario || 'n/a'}}</td>
                <td>${{decision.zone || 'n/a'}}</td>
              `;
              table.appendChild(row);
            }}
          }}

          if (!table.children.length) {{
            table.innerHTML = '<tr><td colspan="6">No active decision signals.</td></tr>';
          }}

          const decisionContent = document.getElementById('decision-content');
          if (snapshot) {{
            decisionContent.innerHTML = `
              <div><strong>${{snapshot.pair}}</strong> on ${{snapshot.exchange}}</div>
              <div class="${{snapshot.decision.signal === 'buy' ? 'status-buy' : 'status-sell'}}" style="font-size: 22px; margin-top: 6px;">
                ${{snapshot.decision.signal.toUpperCase()}} (${{snapshot.decision.confidence}}%)
              </div>
              <div class="meta" style="margin-top: 8px;">${{snapshot.decision.scenario || 'n/a'}} · ${{snapshot.decision.zone || 'n/a'}}</div>
            `;
          }} else {{
            decisionContent.textContent = 'Waiting for analysis...';
          }}
        }} catch (err) {{
          console.error(err);
        }}
      }}

      refreshData();
      setInterval(refreshData, 10000);
    </script>
  </body>
</html>"""

        return Handler


    def start(self):
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()
        self.logger.info('web interface listening on port %s', self.port)


    def update(self, latest):
        self.state['latest'] = latest
