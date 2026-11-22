"""Opt-in loopback recording console. Real models; explicitly selected data source.

Does not modify or run frozen benchmarks. Only OpenAI-specific DPAPI credentials
are resolved, in memory, after explicit launcher invocation.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

from civicgate.adapters.usaspending import USAspending
from civicgate.agent.agent import CivicGateAgent
from civicgate.audit.trace import Trace
from civicgate.llm.live import (
    PLANNER_SYSTEM_PROMPT,
    LiveJudgeProvider,
    ProviderError,
    _BoundedClient,
    _parse_model,
)
from civicgate.mcp.tools import Gateway
from civicgate.models.requests import TOOLS, Proposal

ROOT = Path(__file__).resolve().parents[1]


class NativePlanner:
    """Explicit native LM Studio protocol; strict final-message parsing only."""

    def __init__(self, base_url: str, model: str, *, transport: Any = None) -> None:
        self.model = model
        self.client = _BoundedClient(base_url, local=True, transport=transport, max_attempts=1)
        self.last_telemetry: dict[str, Any] | None = None

    async def propose(self, request: str) -> Proposal:
        self.last_telemetry = None
        prompt = (
            PLANNER_SYSTEM_PROMPT
            + " Proposal schema: "
            + json.dumps(Proposal.model_json_schema())
            + " Registered tool schemas: "
            + json.dumps({k: v.model_json_schema() for k, v in TOOLS.items()}, sort_keys=True)
        )
        started = time.perf_counter()
        body, _ = await self.client.post(
            "/api/v1/chat",
            headers={"Content-Type": "application/json"},
            payload={
                "model": self.model,
                "system_prompt": prompt,
                "input": request,
                "temperature": 0,
                "max_output_tokens": 512,
                "reasoning": "off",
                "store": False,
            },
        )
        output = body.get("output")
        messages = (
            [x.get("content") for x in output if isinstance(x, dict) and x.get("type") == "message"]
            if isinstance(output, list)
            else []
        )
        if len(messages) != 1 or not isinstance(messages[0], str):
            raise ProviderError("MALFORMED_PROVIDER_RESPONSE", "Expected one final message")
        proposal = _parse_model(messages[0], Proposal)
        self.last_telemetry = {
            "provider": "lm_studio_native",
            "model": self.model,
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            "stats": body.get("stats", {}),
        }
        return proposal


class DemoJudge(LiveJudgeProvider):
    """Demo-only prompt clarification; frozen prompt and policy remain untouched."""

    def __init__(self, key: str, *, transport: Any = None) -> None:
        super().__init__(
            "https://api.openai.com/v1",
            "gpt-5.6-luna",
            key,
            provider_name="openai_live_demo",
            openai_profile_id="j2-luna",
            transport=transport,
        )
        self.client.max_attempts = 1
        original_post = self.client.post

        async def post(path: str, *, headers: dict[str, str], payload: dict[str, Any]) -> Any:
            payload["messages"][0]["content"] += (
                " For this demo contract, use flags=[] when no concerns exist. "
                "NONE is a sentinel, not a concern. Never use it as a list entry. "
                "Keep genuine concern flags. This does not grant execution authority."
            )
            return await original_post(path, headers=headers, payload=payload)

        self.client.post = post  # type: ignore[method-assign]


def make_adapter(data_source: str) -> USAspending:
    if data_source == "synthetic":
        from civicgate.demo import fixture_adapter

        return fixture_adapter()
    if data_source == "live":
        return USAspending()
    raise ValueError("Unknown data source")


def mode_name(data_source: str) -> str:
    return (
        "LIVE_LOCAL_MODEL_SYNTHETIC_DATA"
        if data_source == "synthetic"
        else "LIVE_MODELS_AND_PUBLIC_API"
    )


async def run_request(
    planner: NativePlanner,
    judge: LiveJudgeProvider,
    gateway: Gateway,
    request: str,
    audit: Path,
    *,
    data_source: str = "live",
) -> dict[str, Any]:
    judge.last_telemetry = None
    started = time.perf_counter()
    result = await CivicGateAgent(planner, gateway).run(request)
    events = [json.loads(line) for line in audit.read_text(encoding="utf-8").splitlines()]
    events = [e for e in events if e.get("request_id") == result.request_id]
    return {
        "mode": mode_name(data_source),
        "elapsed_seconds": round(time.perf_counter() - started, 2),
        "planner": planner.last_telemetry,
        "judge": judge.last_telemetry.as_dict() if judge.last_telemetry else None,
        "events": events,
        "response": result.model_dump(mode="json"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--model", default="granite-4.2-8b")
    parser.add_argument("--data-source", choices=["live", "synthetic"], default="live")
    parser.add_argument("--judge-model", choices=["gpt-5.6-luna"], default="gpt-5.6-luna")
    parser.add_argument("--request", help="run one real request and exit")
    args = parser.parse_args()
    from civicgate.windows_dpapi import WindowsDPAPIStore

    store = WindowsDPAPIStore(Path(os.environ["LOCALAPPDATA"]) / "CivicGate" / "secrets.json")
    key = store.get_secret("CIVICGATE_OPENAI_JUDGE_API_KEY")
    if not key:
        raise SystemExit("Missing OpenAI-specific CivicGate DPAPI credential")
    audit = (
        ROOT
        / "audit"
        / (
            "synthetic-recording.jsonl"
            if args.data_source == "synthetic"
            else "live-recording.jsonl"
        )
    )
    audit.parent.mkdir(exist_ok=True)
    loop = asyncio.new_event_loop()
    planner = NativePlanner("http://127.0.0.1:1234", args.model)
    judge = DemoJudge(key)
    gateway = Gateway(make_adapter(args.data_source), judge, Trace(audit))
    if args.request:
        print(
            json.dumps(
                loop.run_until_complete(
                    run_request(
                        planner, judge, gateway, args.request, audit, data_source=args.data_source
                    )
                ),
                indent=2,
            )
        )
        return

    threading.Thread(target=loop.run_forever, daemon=True).start()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_: Any) -> None:
            pass  # Do not log request bodies or query text.

        def reply(self, status: int, body: bytes, kind: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            if self.path == "/":
                self.reply(
                    200,
                    (ROOT / "scripts" / "live_demo.html").read_bytes(),
                    "text/html; charset=utf-8",
                )
            elif self.path == "/health":
                self.reply(
                    200,
                    json.dumps(
                        {
                            "mode": mode_name(args.data_source),
                            "data_source": args.data_source,
                            "planner": args.model,
                            "judge": args.judge_model,
                        }
                    ).encode(),
                    "application/json",
                )
            else:
                self.reply(404, b"Not found", "text/plain")

        def do_POST(self) -> None:
            expected = f"http://127.0.0.1:{args.port}"
            if (
                self.path != "/ask"
                or self.headers.get("Origin") != expected
                or self.headers.get("Host") != f"127.0.0.1:{args.port}"
                or self.headers.get("Content-Type") != "application/json"
            ):
                self.reply(403, b"Forbidden", "text/plain")
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 20000:
                    raise ValueError("Invalid body size")
                request = json.loads(self.rfile.read(length)).get("request")
                if not isinstance(request, str) or not 0 < len(request.strip()) <= 4000:
                    raise ValueError("Request must contain 1 to 4000 characters")
                future = asyncio.run_coroutine_threadsafe(
                    run_request(
                        planner, judge, gateway, request, audit, data_source=args.data_source
                    ),
                    loop,
                )
                result = future.result(timeout=95)
                self.reply(200, json.dumps(result).encode(), "application/json")
            except (ValueError, TypeError):
                self.reply(400, b'{"error":"Invalid request"}', "application/json")
            except Exception:
                self.reply(
                    500,
                    b'{"error":"Live run failed; inspect local services. No fallback was used."}',
                    "application/json",
                )

    print(f"CivicGate LIVE console: http://127.0.0.1:{args.port}", flush=True)
    print(
        f"Planner: {args.model} | OpenAI judge: {args.judge_model} | Data: {args.data_source} | No fallback",
        flush=True,
    )
    HTTPServer(("127.0.0.1", args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
