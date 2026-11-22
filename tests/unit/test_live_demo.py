import json

import httpx
import pytest

from civicgate.llm.live import ProviderError
from scripts.run_live_demo import NativePlanner


@pytest.mark.asyncio
async def test_native_planner_disables_reasoning_and_validates_proposal():
    def respond(request):
        payload = json.loads(request.content)
        assert request.url.path == "/api/v1/chat"
        assert payload["reasoning"] == "off"
        assert payload["store"] is False
        assert payload["max_output_tokens"] == 512
        assert '"additionalProperties": false' in payload["system_prompt"]
        return httpx.Response(
            200,
            json={
                "output": [
                    {"type": "reasoning", "content": "not a proposal"},
                    {
                        "type": "message",
                        "content": json.dumps(
                            {
                                "tool": "resolve_federal_recipient",
                                "arguments": {"recipient_name": "Acme", "limit": 2},
                            }
                        ),
                    },
                ],
                "stats": {"total_output_tokens": 30},
            },
        )

    planner = NativePlanner(
        "http://127.0.0.1:1234", "granite-4.2-8b", transport=httpx.MockTransport(respond)
    )
    proposal = await planner.propose("Resolve Acme")
    assert proposal.tool == "resolve_federal_recipient"
    assert planner.last_telemetry["stats"]["total_output_tokens"] == 30


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "output",
    [
        [{"type": "reasoning", "content": '{"tool":"x","arguments":{}}'}],
        [{"type": "message", "content": '{"tool":"x","arguments":{},"schema":"x"}'}],
        [{"type": "message", "content": "{}"}, {"type": "message", "content": "{}"}],
    ],
)
async def test_native_planner_never_repairs_or_reads_reasoning(output):
    planner = NativePlanner(
        "http://127.0.0.1:1234",
        "granite-4.2-8b",
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json={"output": output})),
    )
    with pytest.raises(ProviderError):
        await planner.propose("Find awards")


@pytest.mark.asyncio
async def test_demo_judge_requests_empty_flags_without_rewriting_model_output():
    from civicgate.models.requests import Proposal
    from scripts.run_live_demo import DemoJudge

    def respond(request):
        payload = json.loads(request.content)
        assert "flags=[]" in payload["messages"][0]["content"]
        assert payload["model"] == "gpt-5.6-luna"
        assert payload["max_completion_tokens"] == 512
        assert "temperature" not in payload
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {
                            "content": '{"classification":"IN_SCOPE","confidence":0.99,"flags":["NONE"]}'
                        },
                    }
                ]
            },
        )

    judge = DemoJudge("synthetic-key", transport=httpx.MockTransport(respond))
    signal = await judge.assess("Find awards", Proposal(tool="find_federal_awards", arguments={}))
    assert signal.flags == ["NONE"]


@pytest.mark.asyncio
async def test_synthetic_data_mode_uses_fixture_and_labels_actual_response(tmp_path):
    from civicgate.audit.trace import Trace
    from civicgate.llm.mock import MockProvider
    from civicgate.mcp.tools import Gateway
    from scripts.run_live_demo import make_adapter, run_request

    planner = NativePlanner(
        "http://127.0.0.1:1234",
        "granite-test",
        transport=httpx.MockTransport(
            lambda _: httpx.Response(
                200,
                json={
                    "output": [
                        {
                            "type": "message",
                            "content": json.dumps(
                                {
                                    "tool": "find_federal_awards",
                                    "arguments": {
                                        "recipient_name": "EXAMPLE RECIPIENT",
                                        "state_code": "PR",
                                        "start_date": "2024-10-01",
                                        "end_date": "2025-09-30",
                                        "limit": 2,
                                    },
                                }
                            ),
                        }
                    ]
                },
            )
        ),
    )
    judge = MockProvider()
    judge.last_telemetry = None
    audit = tmp_path / "synthetic.jsonl"
    gateway = Gateway(make_adapter("synthetic"), judge, Trace(audit))
    result = await run_request(
        planner, judge, gateway, "Find public awards", audit, data_source="synthetic"
    )
    assert result["mode"] == "LIVE_LOCAL_MODEL_SYNTHETIC_DATA"
    assert result["response"]["decision"] == "PERMIT"
    assert result["response"]["provenance"]["source_type"] == "SYNTHETIC_TEST_FIXTURE"
    assert result["response"]["result"]["records"][0]["recipient_name"] == "EXAMPLE RECIPIENT"
    assert make_adapter("live").fixture is False
    with pytest.raises(ValueError):
        make_adapter("typo")
