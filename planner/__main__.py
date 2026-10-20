"""python -m planner [--port N] [--no-browser]

The class planner: a local web page for designing the HammerwatchPlus classes. It serves
planner/web/ and keeps every record as planner/data/<collection>/<id>.json, so edits show
up in git like any other change. Standard library only; binds to 127.0.0.1."""
import argparse
import json
import re
import sys
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
WEB = HERE / "web"
DATA = HERE / "data"
COLLECTIONS = ("classes", "doctrines", "skills", "mods", "weapons", "stacks", "attributes", "reference")
DOC_ID = re.compile(r"^[A-Za-z0-9_-][A-Za-z0-9_.-]{0,119}$")
LOCK = threading.Lock()


def dump(record):
    return json.dumps(record, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def load_all():
    out = {}
    for c in COLLECTIONS:
        out[c] = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in sorted((DATA / c).glob("*.json"))}
    return out


def stamp():
    """Changes whenever a record file is added, removed or rewritten (an edit, a git pull)."""
    files = [p for c in COLLECTIONS for p in (DATA / c).glob("*.json")]
    return f"{len(files)}-{max((p.stat().st_mtime_ns for p in files), default=0)}"


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(WEB), **kw)

    def log_message(self, fmt, *args):
        if self.command != "GET":   # the page polls /api/stamp; only edits are worth a line
            sys.stderr.write("%s %s\n" % (self.command, self.path))

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def reply(self, code, body=None):
        raw = json.dumps(body if body is not None else {}).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def record_path(self):
        parts = self.path.split("?")[0].strip("/").split("/")
        if len(parts) != 3 or parts[0] != "api" or parts[1] not in COLLECTIONS or not DOC_ID.match(parts[2]):
            return None
        return DATA / parts[1] / (parts[2] + ".json")

    def same_origin(self):
        # Another site open in the browser must not be able to write here.
        origin = self.headers.get("Origin")
        return origin is None or origin == "http://" + self.headers.get("Host", "")

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/api/data":
            with LOCK:
                return self.reply(200, {"stamp": stamp(), "data": load_all()})
        if path == "/api/stamp":
            return self.reply(200, {"stamp": stamp()})
        if path == "/icons.png" and (WEB / "icons.local.png").exists():
            # cut from the local HoH1 art (git-ignored), in place of the committed placeholders
            self.path = "/icons.local.png"
        return super().do_GET()

    def do_PUT(self):
        p = self.record_path()
        if p is None or not self.same_origin():
            return self.reply(400, {"error": "bad_request"})
        try:
            record = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        except ValueError:
            return self.reply(400, {"error": "bad_json"})
        if not isinstance(record, dict):
            return self.reply(400, {"error": "bad_json"})
        record.pop("_id", None)
        with LOCK:
            p.parent.mkdir(exist_ok=True)
            p.write_text(dump(record), encoding="utf-8", newline="\n")
            return self.reply(200, {"stamp": stamp()})

    def do_DELETE(self):
        p = self.record_path()
        if p is None or not self.same_origin():
            return self.reply(400, {"error": "bad_request"})
        with LOCK:
            if not p.exists():
                return self.reply(404, {"error": "not_found"})
            p.unlink()
            return self.reply(200, {"stamp": stamp()})


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m planner", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", type=int, default=8737, help="port to serve on (default 8737; 0 picks a free one)")
    ap.add_argument("--no-browser", action="store_true", help="don't open the page in a browser")
    a = ap.parse_args(argv)
    try:
        server = ThreadingHTTPServer(("127.0.0.1", a.port), Handler)
    except OSError:
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)   # the port is taken: any free one
    url = f"http://127.0.0.1:{server.server_address[1]}/"
    print(f"Class planner: {url}  (data in {DATA}; Ctrl+C to stop)", flush=True)
    if not a.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
