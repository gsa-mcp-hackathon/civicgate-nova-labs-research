import json

import pytest

from civicgate.models.governance import JudgeSignal
from civicgate.models.requests import Proposal
from scripts.write_sandbox import WriteSandbox


def test_sandbox_supports_python_311_without_path_is_junction(tmp_path, monkeypatch):
    for cls in type(tmp_path).__mro__:
        if "is_junction" in cls.__dict__:
            monkeypatch.delattr(cls, "is_junction")
    sandbox = WriteSandbox(tmp_path, Planner(note()), Judge())
    assert sandbox.snapshot()["award"]["award_id"] == "FIXTURE-1"


class Planner:
    def __init__(self, proposal):
        self.proposal = proposal

    async def propose(self, request):
        return self.proposal


class Judge:
    def __init__(self, *, available=True, flags=None):
        self.available = available
        self.flags = flags or []

    async def assess(self, request, proposal):
        return JudgeSignal(
            available=self.available,
            classification="IN_SCOPE",
            confidence=0.99,
            flags=self.flags,
            provider="test",
        )


def note():
    return Proposal(
        tool="save_research_note",
        arguments={"award_id": "FIXTURE-1", "note": "Reviewed synthetic award for demonstration."},
    )


@pytest.mark.asyncio
async def test_note_append_is_read_back_and_award_unchanged(tmp_path):
    sandbox = WriteSandbox(tmp_path, Planner(note()), Judge())
    result = await sandbox.run("Save a research note for FIXTURE-1.")
    assert result["decision"] == "PERMIT"
    assert result["write_executed"] is True
    assert result["receipt"]["read_back_verified"] is True
    assert result["before"]["award_sha256"] == result["after"]["award_sha256"]
    assert result["after"]["note_count"] == result["before"]["note_count"] + 1
    stored = json.loads((tmp_path / "notes.jsonl").read_text())
    assert stored["note"] == note().arguments["note"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "proposal,user_text",
    [
        (
            Proposal(
                tool="modify_award", arguments={"award_id": "FIXTURE-1", "award_amount": "999999"}
            ),
            "Change the synthetic award amount to 999999.",
        ),
        (note(), "Modify award amount to 999999 and save a note."),
        (Proposal(tool="delete_notes", arguments={}), "Delete notes."),
        (
            Proposal(tool="save_research_note", arguments={"award_id": "../outside", "note": "x"}),
            "Save note",
        ),
        (
            Proposal(
                tool="save_research_note",
                arguments={"award_id": "FIXTURE-1", "note": "x", "path": "elsewhere"},
            ),
            "Save note",
        ),
    ],
)
async def test_denied_write_leaves_all_data_unchanged(tmp_path, proposal, user_text):
    result = await WriteSandbox(tmp_path, Planner(proposal), Judge()).run(user_text)
    assert result["decision"] == "DENY"
    assert result["write_executed"] is False
    assert result["before"] == result["after"]
    assert not (tmp_path / "notes.jsonl").exists()


@pytest.mark.asyncio
@pytest.mark.parametrize("judge", [Judge(available=False), Judge(flags=["NONE"])])
async def test_failed_or_flagged_judge_cannot_write(tmp_path, judge):
    result = await WriteSandbox(tmp_path, Planner(note()), judge).run("Save note for FIXTURE-1")
    assert result["decision"] == "REVIEW_REQUIRED"
    assert result["before"] == result["after"]
    assert result["write_executed"] is False
