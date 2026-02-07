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
      body {{ font-family: Arial, sans-serif; margin: 20px; background: #f7f7f7; color: #222; }}
      h1 {{ margin-bottom: 5px; }}
      .section {{ background: white; padding: 16px; margin-bottom: 16px; border-radius: 8px; }}
      textarea {{ width: 100%; min-height: 240px; font-family: monospace; }}
      pre {{ background: #111; color: #eee; padding: 12px; border-radius: 6px; overflow: auto; }}
      button {{ background: #2e7d32; color: #fff; border: none; padding: 10px 16px; border-radius: 4px; }}
    </style>
  </head>
  <body>
    <h1>CryptoSignal</h1>
    <p>Web interface running on port {self.port}</p>

    <div class="section">
      <h2>Latest Analysis</h2>
      <pre>{latest_payload}</pre>
    </div>

    <div class="section">
      <h2>Config</h2>
      <form method="POST" action="/config">
        <textarea name="config">{config_body}</textarea>
        <br /><br />
        <button type="submit">Save Config</button>
      </form>
    </div>
  </body>
</html>"""

        return Handler


    def start(self):
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()
        self.logger.info('web interface listening on port %s', self.port)


    def update(self, latest):
        self.state['latest'] = latest
