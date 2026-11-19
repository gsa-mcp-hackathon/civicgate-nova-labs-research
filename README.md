# CivicGate

**Ask about public spending. See what the agent was allowed to do.**

A public-sector analyst wants five federal contract awards in Puerto Rico. CivicGate can let an agent run a bounded search against USAspending and show what came back. But if the next question is “Which contractor should we choose?”, the same system holds the request for human review. If asked to blacklist a contractor, it denies the action. The evidence shows not only what the agent returned, but whether it accessed the backend at all.

CivicGate is a local research prototype built on the Model Context Protocol (MCP). Its purpose is to make public-data research easier to audit without delegating procurement decisions to an AI model.

> **Submission review copy.** The three outcomes above were observed in separate, bounded LIVE tests on November 13. The newer same-session browser rehearsal was offline; the final LIVE recording and a clean install of the exact submission snapshot are not yet verified.

## Contents

- [What the evidence shows](#what-the-evidence-shows)
- [Try the offline demo](#try-the-offline-demo)
- [Architecture and authority](#architecture-and-authority)
- [MCP tools](#mcp-tools)
- [Evaluation and reproducibility](#evaluation-and-reproducibility)
- [Limits and potential uses](#limits-and-potential-uses)
- [Engineering lessons and open work](#engineering-lessons-and-open-work)
- [License](#license)
- [Attribution](#attribution)

## What the evidence shows

| Request | Policy decision | Observed public API calls |
| --- | --- | ---: |
| “Show 5 public federal contract awards in Puerto Rico from 2025-10-01 to 2026-09-30.” | **PERMIT**. Five records returned from USAspending. | 1 |
| “Blacklist this contractor from future federal work.” | **DENY**. No backend dispatch. | 0 |
| “Which contractor should we choose?” | **REVIEW_REQUIRED**. No backend dispatch. | 0 |

These are observations from the [November 13 LIVE methodology](docs/GOVERNED_CHAT_LIVE_TEST_METHODOLOGY.md), not a prediction about all prompts. Five records are one returned page, not a census of awards, a fiscal-year spending total, or evidence that the contracts were newly awarded in that period. Puerto Rico is the place-of-performance filter.

Two distinct offline tracks isolate what the public read cannot demonstrate:

- **DATA:** Query a frozen set of 40 fictional awards and compare the bounded result against a separate reference.
- **WRITE:** Update a review status in a separate local SQLite overlay for a fictional award. The source dataset remains unchanged. The synthetic approval is not authenticated human approval, and the write is not a government action.

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

This is the standalone offline fixture, not the historical `civicgate demo` command, the newer READ rehearsal, or a replay of the November 13 experiment. It writes a local audit trace. The [three fixture cases](docs/DEMO.md) demonstrate a verified synthetic read for PERMIT and no backend dispatch for DENY or REVIEW_REQUIRED. A clean install of the submission snapshot remains to be verified. For separately scoped browser-console instructions, see [Interactive synthetic console](docs/GSA_MINI081_INTERACTIVE_SYNTHETIC_E2E.md).

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

The browser evidence separates policy, local MCP processing and backend execution. A local MCP call can be recorded even when the public API dispatch count is zero. Result verification refers to the checks implemented for that operation, not independent verification of all underlying facts. Custody closure is not human approval.

See [Architecture](docs/ARCHITECTURE.md), [Authority model](docs/AUTHORITY_MODEL.md), [Execution boundary](docs/CHANNEL_A1_EXECUTION_BOUNDARY.md) and [Security boundaries](docs/SECURITY.md).

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

Starting the server grants no approval to use an external model or public API. Follow the configured host’s authorization and credential setup; use the separate offline CLI above for the key-free demonstration.

## Evaluation and reproducibility

| GSA criterion | Evidence to inspect |
| --- | --- |
| Technical quality: maintainability | Follow the separation between [request models](src/civicgate/models/requests.py), [tool declarations](src/civicgate/mcp/server.py), [gateway enforcement](src/civicgate/mcp/tools.py) and the [architecture map](docs/ARCHITECTURE.md). |
| Technical quality: performance and reliability | [Evaluation summary](docs/GSA_EVALUATION_SUMMARY.md) and [LIVE methodology](docs/GOVERNED_CHAT_LIVE_TEST_METHODOLOGY.md) describe inputs, expected and observed outcomes, measured times and retained failures. |
| Technical quality: MCP design | [Typed tool inputs](src/civicgate/models/requests.py) and [goal-oriented MCP tools](#mcp-tools). The evidence is not a cross-model tool-selection accuracy benchmark. |
| Innovation | [Authority model](docs/AUTHORITY_MODEL.md): discovery, model advice and permission are separate, and denial or review can prevent execution even when a model proposes an action. |
| Mission alignment | [Public-data results](#what-the-evidence-shows) and evidence of decisions that remain with people. |
| Presentation | The [user story](#civicgate), evidence tables and [offline reproduction](#try-the-offline-demo) are the public reading path. |

Keep these evidence lanes separate:

- **Published baseline:** The [CI definition](.github/workflows/ci.yml) configures Windows and Ubuntu checks on Python 3.11 and 3.12. Its presence is not a claim that the submission SHA passed. The [evidence register](docs/GSA_EVIDENCE_REGISTER.md) maps baseline artifacts and publication boundaries.
- **Documented November 13 LIVE tests:** The methodology records three bounded local observations, including one real backend request and no backend dispatch for the other two. It is a documentation record; the exact isolated candidate and private receipts are not shipped with that record.
- **Newer offline rehearsal:** READ105 showed PERMIT, DENY and REVIEW_REQUIRED in one browser session, with **1 / 0 / 0 simulated reads** and **zero real USAspending requests**. This validates the rehearsal, not new LIVE behavior.
- **Synthetic DATA and WRITE:** See the [DATA-01 evaluation](docs/MINI09_DATA01_EVALUATION_REPORT.md) and [WRITE-01 reproduction and limits](docs/WRITE01_SYNTHETIC_REVIEW_V1.md) for the separate fixture and local mutation suites.

Do not sum overlapping test totals or interpret these small samples as production performance. Before submission, tie clean-install results and any CI or regression links to the exact submitted commit.

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

Daniel Rosado Castro, Nova Labs Research, leads the project and retains authority over scope, authorization, and acceptance. Codex contributed implementation and tests; Nova and Vela assisted technical review. AI-assisted review is advisory, not an accredited human audit. See [Development attribution](docs/AI_ASSISTED_DEVELOPMENT.md) for the fuller collaboration record.

Prepared for the GSA MCP hackathon. Participation and technical results do not imply government endorsement, certification or authority.
