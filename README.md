# CivicGate

**Ask about public spending. See what the agent was allowed to do.**

A public-sector analyst wants five federal contract awards in Puerto Rico. CivicGate can let an agent run a bounded search against USAspending and show what came back. But if the next question is “Which contractor should we choose?”, the same system holds the request for human review. If asked to blacklist a contractor, it denies the action. The evidence shows not only what the agent returned, but whether it accessed the backend at all.

CivicGate is a local research prototype built on the Model Context Protocol (MCP). Its purpose is to make public-data research easier to audit without delegating procurement decisions to an AI model.

[![CI — CivicGate validation](https://github.com/gsa-mcp-hackathon/civicgate-nova-labs-research/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/gsa-mcp-hackathon/civicgate-nova-labs-research/actions/workflows/ci.yml?query=branch%3Amain) · [R3.2 regression evidence — snapshot `795a3242`](https://github.com/gsa-mcp-hackathon/civicgate-nova-labs-research/actions/runs/44570715120/job/135724663393#step:11:1)

> **Submission review copy.** The three outcomes above were observed in separate, bounded LIVE tests on November 13. The earlier READ105 same-session browser rehearsal was offline; the latest local recording uses real Granite planning and an OpenAI judge, with data sources distinguished below. Clean-install and key-free offline-demo checks are verified in CI for snapshot `795a3242`, within the configuration described below. The video prepared for separate Qualtrics submission is not a GitHub artifact or CI evidence.

## Contents

- [For judges](#for-judges)
- [Results at a glance](#results-at-a-glance)
- [Architecture and authority](#architecture-and-authority)
- [Post-submission MCP annotation research](#post-submission-mcp-annotation-research--november-25-2026)
- [MCP tools](#mcp-tools)
- [Try the offline demo](#try-the-offline-demo)
- [Evaluation and reproducibility](#evaluation-and-reproducibility)
- [Limits and potential uses](#limits-and-potential-uses)
- [Engineering lessons and open work](#engineering-lessons-and-open-work)
- [License](#license)
- [Attribution](#attribution)

## For judges

| GSA criterion | Open this | What it shows |
| --- | --- | --- |
| Technical quality | [Key-free offline reproduction](#try-the-offline-demo), [typed MCP tools](#mcp-tools), [pinned CI run](https://github.com/gsa-mcp-hackathon/civicgate-nova-labs-research/actions/runs/44570715120) | Bounded inputs, dispatch controls and repeatable synthetic checks for the identified snapshot. |
| Innovation | [Authority model](docs/AUTHORITY_MODEL.md), [execution boundary](docs/CHANNEL_A1_EXECUTION_BOUNDARY.md) | Model proposals and semantic advice remain separate from deterministic permission and exact execution binding. |
| Mission alignment | [Historical public-data methodology](docs/GOVERNED_CHAT_LIVE_TEST_METHODOLOGY.md), [potential use cases](docs/POTENTIAL_USE_CASES.md) | Public spending research with explicit limits; procurement decisions remain with people. Proposed uses are not deployed capabilities. |
| Presentation | [Results and limits](#results-at-a-glance), [three-case offline demo](docs/DEMO.md), [evaluation summary](docs/GSA_EVALUATION_SUMMARY.md) | A short path from the user story to reproducible behavior and evidence. The demo video is for separate Qualtrics submission only, not hosted in this repository. |

## Results at a glance

| Measure | Result | What it does not show |
| --- | --- | --- |
| [Historical public READ — November 13](docs/GOVERNED_CHAT_LIVE_TEST_METHODOLOGY.md) | One PERMIT run made one USAspending request and returned five records. | A fresh run, a census, a fiscal-year total, or newly awarded contracts throughout that period. |
| [Historical negative cases — November 13](docs/GOVERNED_CHAT_LIVE_TEST_METHODOLOGY.md) | Separate DENY and REVIEW_REQUIRED runs each made zero backend requests. | A guarantee that every future model response or prompt has the same disposition. |
| [Latest recorded DATA ACCESS — November 21](docs/DEMO_RUN_2026-11-21.md) | Real local Granite 4.2 8B and OpenAI GPT-5.6 Luna reviewed a bounded query; PERMIT returned the fictional EXAMPLE RECIPIENT award for 123.45 with SYNTHETIC_TEST_FIXTURE provenance. No USAspending API was called. | The 40-record DATA-01 evaluation, live government data, or a guarantee that future live model calls produce the same result. |
| [Latest recorded WRITE — November 21](docs/DEMO_RUN_2026-11-21.md) | An explicitly scoped SANDBOX_APPEND_NOTE capability permitted a local research-note append and verified it by read-back. An attempted fictional award-amount change was denied; award and notes stayed unchanged on that denial. | A government write, the SQLite WRITE-01 review-status operation, or a write tool in the official MCP registry. |
| [Historical synthetic DATA-01](docs/MINI09_DATA01_EVALUATION_REPORT.md) | Reads over 40 fictional awards are checked against a separate reference. | Live government data, general model accuracy or a production workload. |
| [Historical synthetic WRITE-01](docs/WRITE01_SYNTHETIC_REVIEW_V1.md) | A fictional award's review status changes in a local SQLite overlay; the source dataset stays unchanged. | Authenticated human approval or any write to a government system. |
| [Install and CI — snapshot `795a3242`](https://github.com/gsa-mcp-hackathon/civicgate-nova-labs-research/actions/runs/44570715120) | Five jobs passed. Fresh Ubuntu/Python 3.12 worker installation, `pip check` and the key-free standalone-demo regression passed in CI. | Certification of every dependency selection, a later SHA, live inference or release permission. |

The historical observations come from the linked methodology, not a prediction about all prompts. Puerto Rico is the place-of-performance filter. The installation evidence uses the CI worker configuration described below.

**Keep the demo scopes separate:** public READ uses USAspending; synthetic DATA ACCESS uses fictional records; synthetic WRITE-01 uses a separate local review-state overlay, not government systems. The latest recording is labeled **LIVE LOCAL MODEL · SYNTHETIC DATA** for the synthetic lanes. Granite runs locally; the OpenAI judge is external, so these are not fully offline runs. The DATA ACCESS lane uses the small existing fixture, not the historical 40-record DATA-01 package. The append-note sandbox is a separate local extension, not this repository's SQLite WRITE-01 implementation. The reviewed launchers, UI and mocked-provider tests are included in this branch; private local state and raw receipts are not. See the [recording session report](docs/DEMO_RUN_2026-11-21.md), [READ / DATA ACCESS guide](docs/LIVE_RECORDING.md) and [WRITE sandbox guide](docs/WRITE_SANDBOX_RECORDING.md). These latest demonstrations were checked locally and recorded by the project owner; they are not covered by the pinned official CI run. A direct browser-to-gateway demonstration does not by itself verify MCP transport. The video is for Qualtrics only; it is not included or linked here as implementation or CI evidence.

## Architecture and authority

```text
User request → Bounded tool discovery → Planner proposal
                                              ↓
                                     Governed MCP gateway ← Advisory Judge
                                              ↓
                                   Deterministic policy
                                     /               \
          DENY or REVIEW_REQUIRED: stop       PERMIT: exact execution binding
                                                       ↓
                                         Bounded adapter → Result checks
                                     \                 /
                                     Inspectable evidence
```

**Discovery is not authority.** In local Channel A, the trusted host selects the governing contract before tool discovery. The planner proposes a tool and arguments; an advisory Judge can add semantic evidence, but neither model can change the host’s choice or create execution permission. Deterministic policy decides, and the gateway consumes a binding for the exact authorized call before dispatch. Post-result validation can still withhold an unusable response after PERMIT. A successful HTTP response is not a verified result.

[Agent K](src/civicgate/governance/agent_k.py) is a deterministic behavioral monitor inspired by Officer K from Blade Runner 2049. Operating within CivicGate's governance evaluation path without requiring its own LLM, Agent K detects rule-based indicators of authority overreach, private-data requests, tool-scope violations, and repeated qualifying policy denials. It can also incorporate the advisory Judge's structured ambiguity signal when available.

Agent K produces behavioral signals and containment recommendations but never grants execution authority, overrides policy, or dispatches tools. Known violations can be blocked during preflight, before invoking the external semantic Judge. Deterministic policy makes the authorization decision, while the Gateway enforces the execution boundary.

Agent K observes. Policy decides. Gateway enforces.

The browser evidence separates policy, local MCP processing and backend execution. A local MCP call can be recorded even when the public API dispatch count is zero. Result verification refers to the checks implemented for that operation, not independent verification of all underlying facts. Custody closure is not human approval.

See [Architecture](docs/ARCHITECTURE.md), [Authority model](docs/AUTHORITY_MODEL.md), [Execution boundary](docs/CHANNEL_A1_EXECUTION_BOUNDARY.md) and [Security boundaries](docs/SECURITY.md).

## Post-submission MCP annotation research — November 25, 2026

An external MCP directory/static scan prompted an internal three-stage review of tool metadata. The SDK audit verified all four hints in **22 serialized registrations across six profiles**, while the subsequent semantic review identified **16 closed-profile open-world overstatements** and **one non-additive synthetic WRITE-01 transition**. These are metadata-truthfulness findings, not evidence that the Gateway authorization boundary was bypassed.

The reviewed **MCP_TOOL_METADATA_V2** successor is **opt-in for a trusted host**. It adjusts the SDK-serialized `tools/list` metadata for the supported closed profiles and marks the synthetic review-status update `destructiveHint=true`, retaining conservative WRITE `idempotentHint=false`. The original tool registrations, frozen WRITE-01 v1 sources, execution bindings and policy are unchanged. No new tool, dispatch route, government WRITE or deployment is introduced.

The local review reported **2,798 PASS / 1 SKIP** in the broader core selection, **30 PASS** focused, **487 PASS** in a freshly reproduced regression selection and **48 PASS** Host71 offline; selections overlap and are not summed. These are historical local Windows/Python 3.13 observations, **not** new CI or production certification. The six-profile matrix and publication report are privacy-redacted; raw local captures remain in the separately preserved review package.

Read the [MCP-ANNOTATIONS-03 report](docs/MCP-ANNOTATIONS-03_IMPLEMENTATION_REPORT.md), [22-registration metadata matrix](docs/MCP-ANNOTATIONS-03_METADATA_MATRIX.json), [frozen WRITE-01 integrity summary](docs/MCP-ANNOTATIONS-03_FROZEN_WRITE01_INTEGRITY.json) and [versioned implementation](src/civicgate/mcp/metadata_v2.py). This is a post-submission scientific correction, not a retrospective change to the original hackathon evidence.

## MCP tools

The [FastMCP server](src/civicgate/mcp/server.py) exposes four public READ operations with typed arguments. Their [Pydantic v2 models](src/civicgate/models/requests.py) reject extra fields and enforce constraints such as bounded date ranges, recognized state or territory codes, and integer limits. The [gateway](src/civicgate/mcp/tools.py) validates the proposed arguments before policy evaluation and validates bound arguments before dispatch.

| Tool | Agent-facing task |
| --- | --- |
| `find_federal_awards` | Find a bounded page of awards within specified filters. |
| `get_federal_award` | Retrieve details for a known award identifier. |
| `resolve_federal_recipient` | Surface plausible public recipient matches for disambiguation. A match does not establish legal identity. |
| `summarize_federal_spending` | Summarize amounts in an authorized returned page. A page summary is not a government-wide or fiscal-year total. |

Each tool accepts the original `user_request` and a typed `query`. The original text provides context, not authority. Clients cannot supply trusted Judge signals or policy decisions. The READ contract is bounded to one page, up to 100 awards or 25 recipient candidates, and a date interval of at most 367 calendar days. Searches require at least one recipient, agency, or location filter.

For a compatible MCP host, run the entry point with the installed project's interpreter. Example configuration when `python` resolves to that environment:

```json
{
  "mcpServers": {
    "civicgate": {
      "command": "python",
      "args": ["-m", "civicgate.mcp.server"],
      "env": {"CIVICGATE_AUDIT_PATH": "audit/trace.jsonl"}
    }
  }
}
```

Starting the server grants no approval to use an external model or public API. Follow the configured host’s authorization and credential setup; use the separate offline CLI below for the key-free demonstration.

## Try the offline demo

From a checkout of the CivicGate source, use Python 3.11 or 3.12. The offline demo script uses a local fixture and mocked model behavior; **it does not need provider keys**. Installing dependencies may require access to a package index. Run the demo from a clean shell without provider credentials.

**Windows PowerShell**

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe scripts/offline_demo.py
```

**Linux/macOS**

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/python -m pip check
.venv/bin/python scripts/offline_demo.py
```

This is the standalone offline fixture, not the historical `civicgate demo` command, the newer READ rehearsal, or a replay of the November 13 experiment. It writes a local audit trace. The [three fixture cases](docs/DEMO.md) demonstrate a verified synthetic read for PERMIT and no backend dispatch for DENY or REVIEW_REQUIRED.

For [snapshot `795a3242a351b0cf31e7b70044569106d3f7647f`](https://github.com/gsa-mcp-hackathon/civicgate-nova-labs-research/commit/795a3242a351b0cf31e7b70044569106d3f7647f), the [fresh Ubuntu/Python 3.12 CI job](https://github.com/gsa-mcp-hackathon/civicgate-nova-labs-research/actions/runs/44570715120/job/135724663393) passed installation into a new worker environment, `pip check`, and the core suite containing the [standalone offline-demo regression](tests/adversarial/test_offline_demo.py). That regression checks synthetic PERMIT / DENY / REVIEW_REQUIRED and dispatch only for PERMIT. CI installs `.[dev]` with the pinned worker constraints; this evidence does not certify every platform or a different dependency selection.

For separately scoped browser-console instructions, see [Interactive synthetic console](docs/GSA_MINI081_INTERACTIVE_SYNTHETIC_E2E.md). The newer opt-in Windows recording surfaces have separate guides for [live READ / synthetic DATA ACCESS](docs/LIVE_RECORDING.md) and [synthetic note WRITE](docs/WRITE_SANDBOX_RECORDING.md). They require local model setup and an external OpenAI credential; they are not the key-free offline demo.

## Evaluation and reproducibility

Keep these evidence lanes separate:

- **Published baseline:** [CI run `44570715120`](https://github.com/gsa-mcp-hackathon/civicgate-nova-labs-research/actions/runs/44570715120) passed all five jobs for snapshot `795a3242`: Windows and Ubuntu on Python 3.11 and 3.12, plus the container job. [R3.2 synthetic governance regression](https://github.com/gsa-mcp-hackathon/civicgate-nova-labs-research/actions/runs/44570715120/job/135724663393#step:11:1) is a step within each Python matrix job of [the same CI workflow](.github/workflows/ci.yml), not an independent workflow badge. The badge above follows `main`; these evidence links stay pinned to the tested run. The [dated evidence register](docs/GSA_EVIDENCE_REGISTER.md) maps historical artifacts and publication boundaries.
- **Documented November 13 LIVE tests:** The methodology records three bounded local observations, including one real backend request and no backend dispatch for the other two. It is a documentation record; the exact isolated candidate and private receipts are not shipped with that record.
- **Newer offline rehearsal:** READ105 showed PERMIT, DENY and REVIEW_REQUIRED in one browser session, with **1 / 0 / 0 simulated reads** and **zero real USAspending requests**. This validates the rehearsal, not new LIVE behavior.
- **Latest recorded synthetic DATA ACCESS and WRITE:** The local Granite/OpenAI demonstrations above show fixture access, a permitted note append and a denied award edit. They are separate local demo extensions, not replacements for the historical evaluation packages or proof of the official snapshot's runtime behavior.
- **Historical synthetic DATA and WRITE:** See the [DATA-01 evaluation](docs/MINI09_DATA01_EVALUATION_REPORT.md) and [WRITE-01 reproduction and limits](docs/WRITE01_SYNTHETIC_REVIEW_V1.md) for the separate fixture and local mutation suites.

Do not sum overlapping test totals or interpret these small samples as production performance. Installation, CI and regression evidence above belongs to snapshot `795a3242`; a later submission commit needs its own CI result. These offline checks do not establish new LIVE behavior, model accuracy, or recording/publication permission.

## Limits and potential uses

CivicGate is a prototype for a trusted local host. It does not establish hostile-host isolation, representative production performance, comprehensive model accuracy, or distributed exactly-once delivery. The system does not issue procurement decisions or write to government systems. New applications would need their own tools, authorization policies, data safeguards and evaluations.

[Potential use cases](docs/POTENTIAL_USE_CASES.md) covers where the pattern could be evaluated next. Those examples are not implemented capabilities or claims of compliance.
A separate [platform comparison](docs/PLATFORM_EQUIVALENCE.md) maps potential Databricks and IBM watsonx Orchestrate counterparts. It is a planning reference, not a verified deployment or equivalence claim.

## Engineering lessons and open work

Keep three checks separate: whether a model proposal is well formed, whether policy permits the operation, and whether the backend result passes validation. Earlier runs exposed different failures at each boundary. The [planner lessons](docs/GRANITE_PLANNER_LESSONS_LEARNED.md), [FAA scope findings](docs/MINI09_R021_DISPOSITION_AND_SCOPE_PROPOSAL.md), and [debt register](docs/TECHNICAL_DEBT.md) preserve those distinctions and the open work.

Less manual lookup and clearer review are hypotheses, not measured savings. The [ROI methodology](docs/POTENTIAL_VALUE_AND_ROI.md) records its assumptions and sensitivity cases without claiming a validated return.

## License

CivicGate's original project code is available under the [MIT license](LICENSE-CIVICGATE), Copyright (c) 2026 Daniel Rosado Castro. The organization repository retains its original [GSA MCP Hackathon template notice](LICENSE). These notices identify separate scopes. Third-party material remains subject to its own terms and notices.

## Attribution

Daniel Rosado Castro, Nova Labs Research, leads the project and retains authority over scope, authorization, and acceptance. The owner credits the following AI-assisted contributions:

| Assistant | Contribution |
| --- | --- |
| **Codex** | Implementation, tests, regression investigation and evidence preparation. |
| **Nova (GPT-6)** | Technical review, research advice, governance reasoning and documentation strategy. |
| **Vela (Meta Muse)** | Technical review and engineering assistance, including the historical Databricks Channel B work. |
| **Genie Code** | Helped build and add the historical Databricks Channel B run with Vela; cloud observations remain reported historical evidence, not newly re-executed results. |
| **Hermes Agent (Nous Research)** | Helped build and troubleshoot the latest local demo consoles, integrate local Granite planning with the OpenAI judge, and verify the latest synthetic data-access and sandbox note-write/deny runs for recording. These separately scoped demo additions are included in this branch, without private state or raw receipts. |

Model names are owner-specified attribution labels, not retrospective authentication of every historical session. AI-assisted review is advisory, not an accredited human audit. See the [dated development attribution](docs/AI_ASSISTED_DEVELOPMENT.md) for the earlier collaboration record and its evidence limits.

Prepared for the GSA MCP hackathon. Participation and technical results do not imply government endorsement, certification or authority.
