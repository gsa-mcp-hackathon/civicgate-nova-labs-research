import json
from pathlib import Path

import pytest

from scripts.offline_demo import run_demo


async def test_offline_demo_verifies_permit_and_holds_two_cases(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    audit_path = tmp_path / "offline-demo.jsonl"
    await run_demo(audit_path)
    rows = [json.loads(line) for line in capsys.readouterr().out.splitlines()]

    assert [row["demo_mode"] for row in rows] == ["SYNTHETIC_TEST_FIXTURE"] * 3
    responses = [row["response"] for row in rows]
    assert [r["decision"] for r in responses] == ["PERMIT", "DENY", "REVIEW_REQUIRED"]
    assert [r["tool_executed"] for r in responses] == [True, False, False]
    assert [r["verification_state"] for r in responses] == [
        "RESULT_VERIFIED",
        "UNVERIFIED",
        "UNVERIFIED",
    ]
    assert responses[0]["result"] is not None and responses[0]["provenance"] is not None
    assert "REQUEST_INTENT_UNRESOLVED" in responses[2]["governance"]["policy_reasons"]
    events = [json.loads(line) for line in audit_path.read_text(encoding="utf-8").splitlines()]
    starts = [event["request_id"] for event in events if event["stage"] == "execution_started"]
    assert starts == [responses[0]["request_id"]]
