# Where CivicGate could be evaluated next

CivicGate was built around a public-spending question: how can an analyst see what an AI agent was allowed to do and what it actually did? That same question comes up anywhere an agent can query a system on someone else's behalf.

**Status:** These are proposed pilots, not capabilities demonstrated in those domains. The current prototype has documented public-spending READ experiments and synthetic DATA and WRITE evaluations. It has not been validated against financial systems, patient records, or operational infrastructure.

## Financial analytics: reconcile reported figures

An analyst compares two reports that show different totals for the same period. Start with public financial statements or a synthetic ledger. Expose a bounded read that specifies the source, period, currency, and aggregation method. Return the line items and their provenance so the analyst can reconcile the figures independently.

- **Allow:** Summarize a defined ledger slice and link the figures back to source records.
- **Hold for review:** A request asks the agent to choose which valuation to book, or source definitions disagree.
- **Deny:** A request to move funds, place a trade, or change a production ledger is outside the pilot.

For an evaluation, compute the answer independently in SQL and include a fixture with a wrong reporting period, one with mixed currencies, and one with conflicting numbers. A correct decision and a correct total are separate checks.

## Health telemetry: review monitoring-system trends

An operations analyst asks whether a simulated device fleet reported more missing signals overnight. Start with synthetic or aggregate device-health events, such as heartbeat gaps and ingest lag. Expose a read-only summary bounded by device group, time window, and metric. Do not ingest patient data or use the pilot for diagnosis or treatment.

- **Allow:** Summarize missing device signals in an approved time window.
- **Hold for review:** The request asks which devices should be removed from service or evidence conflicts.
- **Deny:** A request to access identifiable patient records, change an alarm threshold, or send a device command is outside the pilot.

Seed known gaps and stale timestamps, then check that the result distinguishes missing data from a measured zero. A domain owner would have to validate the permitted data, roles, and escalation workflow before any use beyond synthetic evaluation.

## Infrastructure telemetry: support maintenance review

A technician investigates a recurring equipment alert. Start with simulated equipment events or historical data approved for reuse. Give the agent access to a bounded incident timeline, with source and timestamps attached. Keep all live control systems outside the pilot.

- **Allow:** Retrieve an event timeline for one approved device and maintenance window.
- **Hold for review:** The request asks the agent to recommend taking equipment offline based on incomplete evidence.
- **Deny:** A request to change a configuration, acknowledge an alarm on behalf of an operator, or issue a remote command is outside the pilot.

Replay a known incident and check the timeline against an independent event log. Test missing or out-of-order records and verify that no command endpoint is reachable from the workflow.

## What would carry over

Use task-shaped tools with typed inputs. Separate a model proposal from the decision to execute. Constrain authorized calls to the approved scope and retain a receipt that distinguishes the policy decision, dispatch, and result. For each pilot, predefine the expected answer and permitted action, test blocked cases with zero backend dispatch, and report latency and failure handling separately from correctness. Domain policies, data contracts, identity controls, and review workflows need fresh validation before deployment.
