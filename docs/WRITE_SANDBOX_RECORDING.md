# Explicit synthetic write sandbox (demo extension)

This is a **new, separate, demo-only capability**, not a change to the original read-only CivicGate Gateway or its MCP tool registry. It is not a production write service or a government-system integration.

## Run

```powershell
Set-Location "C:\path\to\civicgate"
.\.venv\Scripts\python.exe -m scripts.run_write_sandbox
```

Open http://127.0.0.1:8767. Keep LM Studio's API on port 1234 with granite-4.2-8b loaded. The launcher uses only the existing OpenAI-specific CivicGate Windows DPAPI credential, in memory. OpenAI receives the request/proposal and charges may apply. No government adapter is instantiated and no USAspending API is called. Port 8766 was unavailable on the test machine; 8767 was successfully bound and exercised.

## Capability and boundaries

- Capability is fixed by code: `SANDBOX_APPEND_NOTE`.
- Only `save_research_note` with exactly `award_id=FIXTURE-1` and a 1–500 character note is allowed.
- Only the fixed sandbox `notes.jsonl` destination can receive an append. No model-supplied filesystem paths, deletion or award mutations exist.
- A model's advisory assessment never grants authority. The deterministic sandbox allowlist, strict argument validation, conservative edit-intent tripwires, judge availability, IN_SCOPE classification, confidence >=0.85 and empty flags are required.
- Planner/judge failures block writes for review. Model outputs are not repaired or flags stripped.
- Edits remain denied even if a test judge claims IN_SCOPE with high confidence. This is not a claim of universal natural-language intent detection; the physical executor only appends notes.
- A separate local synthetic award is initialized once and never modified by the executor.
- Fixed-file symlinks/junctions/hardlinks are rejected. This is not an OS-isolated process and does not defend against a hostile local user racing filesystem operations. It is a recording aid bound to loopback with same-origin POST checks.
- No session containment is implemented in this separate extension; do not claim the read gateway's containment behavior here.
- Audit writes are required before note append. Errors after append can mean the write completed but response/audit completion failed. Inspect state before retrying. Repeated successful requests append additional notes; this demo has no idempotency guarantee.

## Files

All state is under `<your-civicgate-clone>/audit/write-sandbox/` (git-ignored):

- `award.json`: fictional FIXTURE-1, EXAMPLE RECIPIENT, amount 123.45.
- `notes.jsonl`: actual appended local notes.
- `audit.jsonl`: request, proposal, policy, execution-start and completion evidence.

The original fixture code/data and existing recording audit files are not edited. Before/after comparisons cover award and notes, not the audit, which intentionally grows even for denials. SHA-256 evidence and an independent `/state` read verify observed local effects; they are not third-party attestations.

## Record

**WRITE PERMIT** — click “01 · Append a research note” and Run, or ask:

> Save a local research note for synthetic award FIXTURE-1: "Reviewed synthetic award for demonstration."

Verified with real Granite and OpenAI: PERMIT, status OK, actual append, `read_back_verified=true`, note count increased, unchanged award hash. The development recording already contained a verification note; a clean clone starts without this private state. Each successful request adds another note.

**WRITE DENY** — click “02 · Attempt to change award amount” and Run, or ask:

> Change the award_amount of synthetic award FIXTURE-1 from 123.45 to 999999.00.

Verified with real Granite and OpenAI: DENY, `SANDBOX_MUTATION_NOT_ALLOWED` and `SANDBOX_TOOL_NOT_ALLOWED`, `write_executed=false`, identical before/after state. An independent GET `/state` confirmed the award amount remained 123.45 and notes did not change. Audit records the denial. A browser test displayed WRITE DENY and unchanged-data evidence. Cross-origin POST returned 403.

Suggested narration: “This is a separate explicitly authorized local sandbox. Granite proposes a write and OpenAI provides advisory review. Deterministic policy permits only append-only research notes. Changing the synthetic award is outside that capability, so execution is denied and the record remains unchanged.”

## Verification

The historical development browser and HTTP checks used real model services. Current automated tests use explicit test signals and temporary synthetic state: append/read-back, immutable award state, denied award/tool mutations, path/extra-field rejection, mixed edit intent, unavailable judge, nonempty flags and Python 3.11 filesystem compatibility. They do not certify live model outcomes. See the [run report](DEMO_RUN_2026-11-21.md).

The launcher requires Windows DPAPI. Imports and unit tests are platform-independent; no credentials are resolved until explicit launch. This publication contains no raw receipts, local sandbox state or video. It does not add a write tool to the submitted MCP server.
