"""
agents/developer_agent.py
Developer Agent — branches, implements, tests, commits, and opens a PR.
"""
from __future__ import annotations

import os
import re
import subprocess
from typing import Any

import anthropic
import structlog

from core.base_agent import BaseAgent
from core.message import Message
from core.state_machine import TicketState
from mcp.github_client import GitHubClient
from mcp.jira_client import JiraClient

logger = structlog.get_logger(__name__)

_IMPL_PROMPT = """\
You are a senior software engineer implementing a JIRA ticket.

Ticket ID: {ticket_id}
Title: {title}
Description:
{description}

Acceptance Criteria:
{acceptance_criteria}

{approach_note}

Instructions:
1. Draft a brief implementation plan (bullet points).
2. List the files you will change and why.
3. Implement the minimal code that satisfies the acceptance criteria.
4. Follow existing code style — do NOT refactor unrelated code.
5. Do NOT introduce new dependencies unless unavoidable.
6. If you discover an unrelated bug, describe it in the "discovered_bugs" field — do not fix it here.

Respond with JSON:
{{
  "plan": "...",
  "files_changed": ["path/to/file.py", ...],
  "implementation_summary": "...",
  "discovered_bugs": ["..."],
  "testing_notes": "..."
}}
"""

_MAX_BUILD_RETRIES = 3


class DeveloperAgent(BaseAgent):
    """
    Picks up READY tickets, implements the changes, and opens a Pull Request.
    """

    name = "developer"

    def __init__(
        self,
        *,
        jira: JiraClient | None = None,
        github: GitHubClient | None = None,
        llm_client: anthropic.AsyncAnthropic | None = None,
        repo_root: str = ".",
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._jira = jira or JiraClient()
        self._github = github or GitHubClient()
        self._llm = llm_client or anthropic.AsyncAnthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY", "")
        )
        self._repo_root = repo_root

    # ── BaseAgent interface ───────────────────────────────────────────────────

    def validate_input(self, message: Message) -> None:
        self.require_fields(message.payload, "ticket_id", "classification")
        if message.payload.get("classification") not in {"READY"}:
            from core.base_agent import InputValidationError
            raise InputValidationError(
                f"Developer Agent only handles READY tickets, "
                f"got: {message.payload.get('classification')!r}"
            )

    async def run(self, message: Message) -> Message:
        ticket_id: str = message.payload["ticket_id"]
        approach_note: str = message.payload.get("selected_approach", "")
        log = self._log.bind(ticket_id=ticket_id)

        # 1. Fetch ticket.
        log.info("developer.fetch_ticket")
        ticket_data = await self._jira.get_ticket(ticket_id)
        fields = ticket_data.get("fields", {})
        title: str = fields.get("summary", "")
        description: str = fields.get("description", "") or ""
        acceptance_criteria: str = fields.get("acceptance_criteria", "") or ""

        # 2. Generate implementation plan.
        log.info("developer.plan")
        impl = await self._plan_implementation(
            ticket_id=ticket_id,
            title=title,
            description=description,
            acceptance_criteria=acceptance_criteria,
            approach_note=approach_note,
            dry_run=message.dry_run,
        )

        # 3. Create branch.
        branch_name = self._branch_name(ticket_id, title)
        log.info("developer.create_branch", branch=branch_name)
        if not message.dry_run:
            await self._github.create_branch(branch_name)

        # 4. Apply changes + run build/tests (up to MAX_BUILD_RETRIES).
        commit_sha = ""
        test_status = "skipped"
        if not message.dry_run:
            commit_sha, test_status = await self._apply_and_verify(
                branch_name=branch_name,
                ticket_id=ticket_id,
                impl=impl,
                log=log,
            )

        # 5. Open PR.
        pr_url = ""
        pr_number = 0
        if not message.dry_run:
            pr_body = self._build_pr_body(ticket_id, impl)
            pr_result = await self._github.create_pr(
                title=f"[{ticket_id}] {title}",
                body=pr_body,
                head=branch_name,
            )
            pr_url = pr_result.get("html_url", "")
            pr_number = pr_result.get("number", 0)

            # 6. Post PR link to JIRA + transition.
            await self._jira.add_comment(ticket_id, f"PR raised: {pr_url}")
            await self._jira.transition(ticket_id, TicketState.CODE_REVIEW.value)

        log.info("developer.done", pr_url=pr_url)
        return message.reply(
            source_agent=self.name,
            target_agent="human",  # Human review gate.
            ticket_state=TicketState.CODE_REVIEW.value,
            payload={
                "ticket_id": ticket_id,
                "branch_name": branch_name,
                "pr_url": pr_url,
                "pr_number": pr_number,
                "commit_sha": commit_sha,
                "test_status": test_status,
                "new_jira_state": TicketState.CODE_REVIEW.value,
                "implementation_summary": impl.get("implementation_summary", ""),
            },
        )

    # ── Internal helpers ──────────────────────────────────────────────────────

    async def _plan_implementation(
        self,
        *,
        ticket_id: str,
        title: str,
        description: str,
        acceptance_criteria: str,
        approach_note: str,
        dry_run: bool,
    ) -> dict[str, Any]:
        if dry_run:
            return {
                "plan": "Dry run — implementation skipped.",
                "files_changed": [],
                "implementation_summary": "Dry run.",
                "discovered_bugs": [],
                "testing_notes": "N/A",
            }
        prompt = _IMPL_PROMPT.format(
            ticket_id=ticket_id,
            title=title,
            description=description,
            acceptance_criteria=acceptance_criteria or "Not provided.",
            approach_note=f"Selected approach: {approach_note}" if approach_note else "",
        )
        response = await self._llm.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        import json
        raw = response.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw)

    async def _apply_and_verify(
        self,
        *,
        branch_name: str,
        ticket_id: str,
        impl: dict[str, Any],
        log: structlog.BoundLogger,
    ) -> tuple[str, str]:
        """Apply implementation, run build + tests.  Returns (commit_sha, test_status)."""
        # In a real deployment, this would write files via the GitHub MCP or local shell.
        # Here we run the project's build/test scripts and retry on failure.
        for attempt in range(1, _MAX_BUILD_RETRIES + 1):
            build_ok = self._run_script("scripts/build.sh")
            if build_ok:
                break
            log.warning("developer.build_failed", attempt=attempt)
            if attempt == _MAX_BUILD_RETRIES:
                await self._jira.transition(ticket_id, TicketState.BLOCKED.value)
                await self._jira.add_comment(ticket_id, "Build failed after 3 attempts — blocked.")
                return "", "build_failed"

        for attempt in range(1, _MAX_BUILD_RETRIES + 1):
            test_ok = self._run_script("scripts/test.sh")
            if test_ok:
                break
            log.warning("developer.test_failed", attempt=attempt)
            if attempt == _MAX_BUILD_RETRIES:
                await self._jira.transition(ticket_id, TicketState.BLOCKED.value)
                await self._jira.add_comment(ticket_id, "Tests failed after 3 attempts — blocked.")
                return "", "test_failed"

        # Commit via GitHub MCP.
        commit_result = await self._github.push_commit(
            branch_name=branch_name,
            message=f"[{ticket_id}] {impl.get('implementation_summary', 'Implement changes')[:60]}",
            files=[],  # Real agent would pass actual file diffs here.
        )
        commit_sha = commit_result.get("sha", "")
        return commit_sha, "passed"

    def _run_script(self, script: str) -> bool:
        """Run a shell script from the repo root. Returns True on success."""
        path = os.path.join(self._repo_root, script)
        if not os.path.exists(path):
            return True  # No script = treat as passing.
        result = subprocess.run(
            ["bash", path],
            cwd=self._repo_root,
            capture_output=True,
            timeout=300,
        )
        return result.returncode == 0

    @staticmethod
    def _branch_name(ticket_id: str, title: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:50]
        return f"{ticket_id.lower()}/{slug}"

    @staticmethod
    def _build_pr_body(ticket_id: str, impl: dict[str, Any]) -> str:
        jira_url = os.environ.get("JIRA_BASE_URL", "")
        files = "\n".join(f"- `{f}`" for f in impl.get("files_changed", []))
        bugs = "\n".join(f"- {b}" for b in impl.get("discovered_bugs", [])) or "None"
        return f"""\
## Summary
{impl.get('implementation_summary', '')}

## JIRA Ticket
[{ticket_id}]({jira_url}/browse/{ticket_id})

## Changes
{files}

## Testing
{impl.get('testing_notes', '')}

## Discovered Bugs (not fixed in this PR)
{bugs}

## Notes for Reviewer
Please review the implementation plan posted in the JIRA ticket before reviewing the diff.
"""
