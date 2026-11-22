"""Run only the explicit local synthetic write sandbox on loopback port 8767."""

import asyncio
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from civicgate.windows_dpapi import WindowsDPAPIStore
from scripts.write_sandbox import SandboxJudge, SandboxPlanner, WriteSandbox

ROOT = Path(__file__).resolve().parents[1]


def main():
    key = WindowsDPAPIStore(
        Path(os.environ["LOCALAPPDATA"]) / "CivicGate" / "secrets.json"
    ).get_secret("CIVICGATE_OPENAI_JUDGE_API_KEY")
    if not key:
        raise SystemExit("OpenAI-specific CivicGate credential missing")
    directory = ROOT / "audit" / "write-sandbox"
    sandbox = WriteSandbox(directory, SandboxPlanner("granite-4.2-8b"), SandboxJudge(key))
    loop = asyncio.new_event_loop()
    threading.Thread(target=loop.run_forever, daemon=True).start()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def reply(self, code, value, kind="application/json"):
            body = value if isinstance(value, bytes) else json.dumps(value).encode()
            self.send_response(code)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == "/":
                self.reply(
                    200,
                    (ROOT / "scripts" / "write_sandbox.html").read_bytes(),
                    "text/html; charset=utf-8",
                )
            elif self.path == "/state":
                self.reply(200, sandbox.snapshot())
            else:
                self.reply(404, {"error": "Not found"})

        def do_POST(self):
            if (
                self.path != "/ask"
                or self.headers.get("Origin") != "http://127.0.0.1:8767"
                or self.headers.get("Host") != "127.0.0.1:8767"
                or self.headers.get("Content-Type") != "application/json"
            ):
                self.reply(403, {"error": "Forbidden"})
                return
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 20000:
                    raise ValueError("Invalid size")
                request = json.loads(self.rfile.read(size)).get("request")
                if not isinstance(request, str) or not 0 < len(request.strip()) <= 4000:
                    raise ValueError("Invalid request")
                result = asyncio.run_coroutine_threadsafe(sandbox.run(request), loop).result(
                    timeout=85
                )
                self.reply(200, result)
            except (ValueError, TypeError):
                self.reply(400, {"error": "Invalid request"})
            except Exception:
                self.reply(
                    500,
                    {
                        "error": "Sandbox run failed. Inspect local audit and state before retrying; a local append may have completed."
                    },
                )

    print("CivicGate WRITE SANDBOX: http://127.0.0.1:8767", flush=True)
    print(
        "Real local Granite | Live OpenAI judge | Synthetic local files only | No government API",
        flush=True,
    )
    HTTPServer(("127.0.0.1", 8767), Handler).serve_forever()


if __name__ == "__main__":
    main()
