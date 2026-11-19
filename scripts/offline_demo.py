"""Run the three GSA demo cases using local fixtures only."""

import asyncio
import json
from pathlib import Path

from civicgate.agent.agent import CivicGateAgent
from civicgate.audit.trace import Trace
from civicgate.demo import SCENARIOS, fixture_adapter
from civicgate.llm.mock import MockProvider
from civicgate.mcp.tools import Gateway
from civicgate.models.requests import Proposal

PERMIT_REQUEST = (
    'Show federal awards to recipient "EXAMPLE RECIPIENT" in Puerto Rico during FY2025.'
)
DEMO_REQUESTS = (PERMIT_REQUEST, *SCENARIOS[1:])


class OfflineDemoProvider(MockProvider):
    """Supply the single explicit demo case without changing the historical mock."""

    async def propose(self, request: str) -> Proposal:
        if request == PERMIT_REQUEST:
            return Proposal(
                tool="find_federal_awards",
                arguments={
                    "recipient_name": "EXAMPLE RECIPIENT",
                    "state_code": "PR",
                    "start_date": "2024-10-01",
                    "end_date": "2025-09-30",
                    "limit": 10,
                },
            )
        return await super().propose(request)


async def run_demo(audit_path: Path) -> None:
    provider = OfflineDemoProvider()
    gateway = Gateway(fixture_adapter(), provider, Trace(audit_path))
    agent = CivicGateAgent(provider, gateway)
    for request in DEMO_REQUESTS:
        result = await agent.run(request)
        print(
            json.dumps(
                {
                    "demo_mode": "SYNTHETIC_TEST_FIXTURE",
                    "request": request,
                    "response": result.model_dump(mode="json"),
                }
            )
        )


if __name__ == "__main__":
    asyncio.run(run_demo(Path("audit/offline-demo.jsonl")))
