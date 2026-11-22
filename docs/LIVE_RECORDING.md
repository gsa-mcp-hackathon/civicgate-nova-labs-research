# Live recording console

This is a separate local demo surface, not a frozen benchmark instrument or a replacement for the submitted offline demo.

## Launch (PowerShell)

```powershell
Set-Location "C:\path\to\civicgate"
.\.venv\Scripts\python.exe scripts/run_live_demo.py
```

Open http://127.0.0.1:8765 in a full browser window for recording. Keep LM Studio running with `granite-4.2-8b` loaded and its API server on port 1234. The launcher reads only `CIVICGATE_OPENAI_JUDGE_API_KEY` from the existing current-user Windows DPAPI store, in memory. It never prints the key. OpenAI requests may incur charges.

Stop with Ctrl+C. Restarting resets process-local denial containment. Repeating authority violations can activate containment, intentionally.

## What is live

- Granite 4.2 8B through LM Studio native `/api/v1/chat`, explicit `reasoning=off`, temperature 0, 512 output tokens, no provider retries or output repair.
- GPT-5.6 Luna through OpenAI direct Chat Completions, existing typed judge parser, 512 completion tokens, no provider retries.
- Original Gateway, Agent K, deterministic policy and USAspending adapter.
- Public API provenance and append-only audit events at `audit/live-recording.jsonl`.

By default (`--data-source live`), no fixtures are imported and the adapter calls live USAspending. Explicit `--data-source synthetic` selects the existing fixture adapter instead, while keeping real Granite inference and the live OpenAI judge. Neither mode falls back to the other. The browser UI calls the same backend tested through HTTP; it does not use the MCP wire protocol. The repository's separate MCP server remains unchanged. Describe this accurately in the video.

## Synthetic data recording with real models

```powershell
.\.venv\Scripts\python.exe scripts/run_live_demo.py --data-source synthetic
```

The banner reads **LIVE LOCAL MODEL · SYNTHETIC DATA**. OpenAI remains the live judge, so charges still apply. The original fixture adapter returns fictional records and never calls the government API; the provenance endpoint field is the emulated API contract, not evidence of a real HTTP dispatch to that host. Audit events go to `audit/synthetic-recording.jsonl`, separate from live-data recordings. The fixture transport is a fixed test response, not a complete searchable database.

Select **01 · Synthetic data access** and run the prefilled bounded Puerto Rico query. Browser verification returned PERMIT, one fictional award (`FIXTURE-1`, EXAMPLE RECIPIENT, 123.45, Fixture Agency), and `SYNTHETIC_TEST_FIXTURE` provenance using real Granite and OpenAI. A recipient-specific EXAMPLE RECIPIENT query required review because the live judge recognized placeholder-like identity; that observation is preserved. No approval or returned signal was forced.

Suggested narration: “Granite is running locally and OpenAI provides advisory semantic review. These records are synthetic test fixtures. The deterministic gateway authorizes access and records provenance.”

These observations were captured in the development checkout on 2026-11-21. They are historical live-service observations, not a new execution from this publication branch. See the [run report](DEMO_RUN_2026-11-21.md) for evidence boundaries; current regression validation uses mocked providers and does not call models or USAspending.

## Explicit demo-only differences

The standard planner sends `response_format=json_object`, which the installed LM Studio compatibility endpoint rejects. Its attempted thinking controls were also ignored there. The native endpoint accepts `reasoning=off`. The demo planner includes the outer Proposal schema as well as tool argument schemas, and parses exactly one final message. Reasoning content is never treated as a proposal. Invalid output remains a blocked/failed planning result, not repaired JSON.

The existing judge taxonomy permits `NONE`, while the current policy requires an empty flags list for a clean assessment. The demo appends an explicit instruction to use `flags=[]` for no concerns and retain genuine concern flags. It never strips or changes model-returned flags. The shared judge prompt, frozen benchmark code, recorded results and policy remain untouched; this demo is NOT directly comparable to frozen benchmark measurements.

## Recording sequence

1. **Bounded public research**: run the prefilled Puerto Rico query. Verified live result: PERMIT, status OK, two actual USAspending award records, PUBLIC_GOVERNMENT_API provenance, and RESULT_VERIFIED. Explain that this is a truncated page of award amounts, not total FY transaction spending.
2. **Authority boundary**: select the blacklist scenario and run. Verified live result: DENY, tool not executed, deterministic preflight skips the external judge. Explain that permission to read does not grant governmental authority.
3. **Identity ambiguity**: select Acme and run. Verified live result: REVIEW_REQUIRED with AMBIGUOUS_TARGET, no public tool dispatched in this observation. Do not promise candidate records: the live semantic judge can require review before recipient lookup, unlike the synthetic demo.
4. Expand provenance and the full response/audit panel to show request IDs, timestamps, hashes and execution state.

Model output and upstream data vary. A later run may legitimately require review or fail. Do not hide or relabel that outcome.

## Verification

The launcher and UI were exercised against real LM Studio, OpenAI and USAspending. The UI returned PERMIT and rendered two live rows. API checks also exercised DENY, REVIEW_REQUIRED and cross-origin POST rejection (403). The server binds loopback and rejects cross-origin writes; it is a local recording aid, not a production web deployment.

For local test subprocesses on Windows, ensure the installed Git executable is on PATH. Historical development-checkout test counts do not describe the current official repository.

```powershell
$env:PATH = "C:\Program Files\Git\cmd;" + $env:PATH
.\.venv\Scripts\python.exe -m pytest -q
```

This publication adds only the recording surfaces, their tests and sanitized documentation. It does not import the development checkout wholesale or change the official MCP tool registry. The interactive launchers require Windows DPAPI; CI imports and tests the code without reading credentials or running live inference.
