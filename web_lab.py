"""Run from the checkout: python3 web_lab.py"""
import argparse
import json
from dataclasses import asdict
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

from rm_tuning_lab.core import simulate
from rm_tuning_lab.plugins import catalog


class Handler(SimpleHTTPRequestHandler):
    def json_response(self, value, status=200):
        body = json.dumps(value, ensure_ascii=False, allow_nan=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urlsplit(self.path)
        cases = self.server.cases
        if url.path == "/api/cases":
            self.json_response({k: dict(title=c.title, group=c.group, unit=c.unit, lesson=c.lesson,
                                        knobs={p: asdict(v) for p, v in c.knobs.items()})
                                for k, c in cases.items()})
        elif url.path == "/api/run":
            try:
                query = {k: v[0] for k, v in parse_qs(url.query).items()}
                case = cases[query.pop("case")]
                self.json_response(simulate(case, {k: float(v) for k, v in query.items()}))
            except (ValueError, KeyError) as error:
                self.json_response({"error": str(error)}, 400)
        else:
            super().do_GET()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plugin", default="")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    handler = partial(Handler, directory=str(Path(__file__).resolve().parent / "static"))
    with ThreadingHTTPServer(("127.0.0.1", args.port), handler) as server:
        server.cases = catalog(args.plugin)
        print(f"http://127.0.0.1:{server.server_port}", flush=True)
        server.serve_forever()


if __name__ == "__main__":
    main()
