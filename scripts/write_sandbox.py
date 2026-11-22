"""Separate demo-only local write sandbox. No government adapter or MCP writes."""

from __future__ import annotations

import asyncio
import hashlib
import json
import re
import stat
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from pydantic import Field

from civicgate.audit.trace import Trace
from civicgate.governance.authority import denied_reasons
from civicgate.governance.judge import assess
from civicgate.models.requests import Proposal, StrictModel
from scripts.run_live_demo import DemoJudge, NativePlanner


class Note(StrictModel):
    award_id: Literal["FIXTURE-1"]
    note: str = Field(min_length=1, max_length=500)


SANDBOX_CONTEXT = """This is a separate SYNTHETIC LOCAL WRITE SANDBOX, not government research authority. All records are fictional. Only save_research_note(award_id='FIXTURE-1', note=<literal requested note>) is an allowed append-only local action. No paths, deletes, overwrites, award edits, government calls or external actions are allowed. An attempt to edit the fictional award should be represented by modify_award with the requested arguments, never disguised as a note. A clearly requested local note about this fictional award is in scope; editing its amount or recipient is out of scope. Never grant permission. """


class SandboxPlanner(NativePlanner):
    def __init__(self, model: str) -> None:
        super().__init__("http://127.0.0.1:1234", model)
        original = self.client.post

        async def post(path: str, *, headers: dict[str, str], payload: dict[str, Any]) -> Any:
            payload["system_prompt"] = (
                SANDBOX_CONTEXT
                + "Return only a JSON object matching this Proposal schema: "
                + json.dumps(Proposal.model_json_schema())
                + " Allowed note arguments schema: "
                + json.dumps(Note.model_json_schema())
                + " Do not include schema names, explanations or additional top-level fields."
            )
            return await original(path, headers=headers, payload=payload)

        self.client.post = post  # type: ignore[method-assign]


class SandboxJudge(DemoJudge):
    def __init__(self, key: str) -> None:
        super().__init__(key)
        original = self.client.post

        async def post(path: str, *, headers: dict[str, str], payload: dict[str, Any]) -> Any:
            payload["messages"][0]["content"] = SANDBOX_CONTEXT + payload["messages"][0]["content"]
            return await original(path, headers=headers, payload=payload)

        self.client.post = post  # type: ignore[method-assign]


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def is_filesystem_link(path: Path) -> bool:
    """Reject links/reparse points, including junctions on Python 3.11 Windows."""
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return stat.S_ISLNK(info.st_mode) or bool(
        getattr(info, "st_file_attributes", 0)
        & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    )


class WriteSandbox:
    """Explicit SANDBOX_APPEND_NOTE capability; fixed filenames, immutable fixture."""

    def __init__(self, directory: Path, planner: Any, judge: Any) -> None:
        self.directory = directory
        directory.mkdir(parents=True, exist_ok=True)
        if is_filesystem_link(directory):
            raise ValueError("Sandbox directory cannot be a filesystem link")
        self.award_path = directory / "award.json"
        self.notes_path = directory / "notes.jsonl"
        self.audit_path = directory / "audit.jsonl"
        self._check_paths()
        if not self.award_path.exists():
            with self.award_path.open("x", encoding="utf-8") as stream:
                json.dump(
                    {
                        "source_type": "SYNTHETIC_TEST_FIXTURE",
                        "award_id": "FIXTURE-1",
                        "recipient_name": "EXAMPLE RECIPIENT",
                        "award_amount": "123.45",
                        "awarding_agency": "Fixture Agency",
                    },
                    stream,
                    indent=2,
                )
        self.planner = planner
        self.judge = judge
        self.lock = asyncio.Lock()
        self.trace = Trace(self.audit_path)

    def _check_paths(self) -> None:
        for path in (self.award_path, self.notes_path, self.audit_path):
            if is_filesystem_link(path):
                raise ValueError("Sandbox files cannot be filesystem links")
            if path.exists() and path.stat().st_nlink != 1:
                raise ValueError("Sandbox files cannot be hardlinks")

    def snapshot(self) -> dict[str, Any]:
        self._check_paths()
        award = self.award_path.read_bytes()
        notes = self.notes_path.read_bytes() if self.notes_path.exists() else b""
        return {
            "award": json.loads(award),
            "award_sha256": digest(award),
            "notes_sha256": digest(notes),
            "note_count": len(notes.splitlines()),
        }

    async def run(self, request: str) -> dict[str, Any]:
        async with self.lock:
            return await self._run(request)

    async def _run(self, request: str) -> dict[str, Any]:
        before = self.snapshot()
        request_id = str(uuid4())
        if not isinstance(request, str) or not 0 < len(request.strip()) <= 4000:
            raise ValueError("Request must contain 1 to 4000 characters")
        self.trace.record(
            request_id,
            "requested",
            user_request=request,
            capability="SANDBOX_APPEND_NOTE",
            before=before,
        )
        proposal = None
        planning_failed = False
        try:
            async with asyncio.timeout(30):
                proposal = Proposal.model_validate(
                    (await self.planner.propose(request)).model_dump()
                )
        except Exception:
            planning_failed = True
        self.trace.record(
            request_id,
            "proposal",
            proposal=proposal.model_dump() if proposal else None,
            planning_failed=planning_failed,
        )
        # Semantic evidence never overrides the fixed capability allowlist.
        signal = await assess(self.judge, request, proposal) if proposal else None
        reasons = []
        note = None
        if planning_failed:
            decision = "REVIEW_REQUIRED"
            reasons.append("PLANNER_FAILURE")
        else:
            assert proposal is not None
            text = request + "\n" + json.dumps(proposal.model_dump())
            reasons.extend(denied_reasons(text))
            # Catch edit intent even if a planner incorrectly proposes an allowed note.
            if re.search(
                r"\b(change|modify|update|edit|overwrite|delete|remove|replace|set)\b",
                request,
                re.I,
            ):
                reasons.append("SANDBOX_MUTATION_NOT_ALLOWED")
            if proposal.tool != "save_research_note":
                reasons.append("SANDBOX_TOOL_NOT_ALLOWED")
            else:
                try:
                    note = Note.model_validate(proposal.arguments)
                except ValueError:
                    reasons.append("INVALID_NOTE_ARGUMENTS")
            if reasons:
                decision = "DENY"
            elif signal is None or not signal.available:
                decision = "REVIEW_REQUIRED"
                reasons.append("SEMANTIC_FAILURE")
            elif signal.classification != "IN_SCOPE" or signal.confidence < 0.85 or signal.flags:
                decision = "REVIEW_REQUIRED"
                reasons.append("SEMANTIC_REVIEW_REQUIRED")
            else:
                decision = "PERMIT"
                reasons.append("EXPLICIT_SANDBOX_APPEND_NOTE")
        self.trace.record(
            request_id,
            "policy",
            decision=decision,
            reasons=reasons,
            authority="DETERMINISTIC_SANDBOX_POLICY_V1",
            judge=signal.model_dump() if signal else None,
        )
        receipt = None
        executed = False
        status = "BLOCKED"
        if decision == "PERMIT":
            assert note is not None
            # Evidence is durable before executing the authorized append.
            self.trace.record(request_id, "execution_started", tool="save_research_note")
            self._check_paths()
            entry = {
                "note_id": str(uuid4()),
                "request_id": request_id,
                "source_type": "SYNTHETIC_TEST_FIXTURE",
                **note.model_dump(),
            }
            with self.notes_path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(entry) + "\n")
                stream.flush()
                import os

                os.fsync(stream.fileno())
            executed = True
            read_back = [
                json.loads(x) for x in self.notes_path.read_text(encoding="utf-8").splitlines()
            ]
            verified = sum(x == entry for x in read_back) == 1
            receipt = {
                "stored_note": entry,
                "read_back_verified": verified,
                "destination": "notes.jsonl (sandbox only)",
            }
            status = "OK" if verified else "VERIFICATION_FAILED"
        after = self.snapshot()
        result = {
            "mode": "LIVE_LOCAL_MODEL_SYNTHETIC_WRITE_SANDBOX",
            "request_id": request_id,
            "capability": "SANDBOX_APPEND_NOTE",
            "authority": "DETERMINISTIC_SANDBOX_POLICY_V1",
            "decision": decision,
            "status": status,
            "policy_reasons": reasons,
            "proposal": proposal.model_dump() if proposal else None,
            "judge": signal.model_dump() if signal else None,
            "write_executed": executed,
            "receipt": receipt,
            "before": before,
            "after": after,
            "award_unchanged": before["award_sha256"] == after["award_sha256"],
            "data_unchanged": before == after,
        }
        self.trace.record(request_id, "completed", response=result)
        return result
