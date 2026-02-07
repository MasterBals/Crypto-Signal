#!/usr/local/bin/python
"""Backend API server for Crypto Signal."""

import threading
import time
from datetime import datetime, timezone

from flask import Flask, jsonify

import logs
import structlog
from conf import Configuration
from exchange import ExchangeInterface
from notification import Notifier
from behaviour import Behaviour


class BackendRunner:
    """Runs the analysis loop and stores the latest results."""

    def __init__(self, config):
        self.config = config
        self.settings = config.settings
        self.logger = structlog.get_logger()
        self.exchange_interface = ExchangeInterface(config.exchanges)
        self.notifier = Notifier(config.notifiers)
        self.behaviour = Behaviour(config, self.exchange_interface, self.notifier)
        self.lock = threading.Lock()
        self.last_result = None
        self.last_run = None

    def run_once(self):
        """Run analysis once and store normalized results."""
        market_pairs = self.settings["market_pairs"]
        output_mode = "none"
        raw_result = self.behaviour._test_strategies(market_pairs, output_mode)
        normalized = normalize_results(raw_result)
        with self.lock:
            self.last_result = normalized
            self.last_run = datetime.now(timezone.utc).isoformat()
        return normalized

    def get_snapshot(self):
        """Return a snapshot of the last result and run time."""
        with self.lock:
            return self.last_result, self.last_run


def normalize_results(results):
    """Convert pandas dataframes to plain dictionaries for JSON output."""
    normalized = {}
    for exchange, markets in results.items():
        normalized[exchange] = {}
        for market_pair, payload in markets.items():
            normalized[exchange][market_pair] = normalize_pair(payload)
    return normalized


def normalize_pair(payload):
    normalized = {}
    for key, value in payload.items():
        if key == "decision":
            normalized[key] = value
            continue
        normalized[key] = {}
        for indicator, entries in value.items():
            normalized[key][indicator] = []
            for entry in entries:
                normalized_entry = {
                    "config": entry["config"],
                    "result": {}
                }
                dataframe = entry.get("result")
                if hasattr(dataframe, "to_dict") and not dataframe.empty:
                    normalized_entry["result"] = dataframe.to_dict(orient="records")[-1]
                normalized[key][indicator].append(normalized_entry)
    return normalized


def create_app():
    config = Configuration()
    settings = config.settings
    logs.configure_logging(settings["log_level"], settings["log_mode"])
    runner = BackendRunner(config)

    app = Flask(__name__)

    def background_loop():
        while True:
            try:
                runner.run_once()
            except Exception:
                structlog.get_logger().exception("Backend run failed")
            time.sleep(settings["update_interval"])

    thread = threading.Thread(target=background_loop, daemon=True)
    thread.start()

    @app.after_request
    def apply_headers(response):
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.route("/api/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok"})

    @app.route("/api/results", methods=["GET"])
    def results():
        last_result, last_run = runner.get_snapshot()
        return jsonify({
            "status": "ok",
            "last_run": last_run,
            "results": last_result
        })

    @app.route("/api/run", methods=["POST"])
    def run_now():
        result = runner.run_once()
        last_result, last_run = runner.get_snapshot()
        return jsonify({
            "status": "ok",
            "last_run": last_run,
            "results": last_result
        })

    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=8886)
