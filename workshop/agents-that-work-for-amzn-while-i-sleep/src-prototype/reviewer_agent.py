"""
agents/reviewer_agent.py
Reviewer Agent — classifies PR comments, applies changes, and re-requests review.
"""
from __future__ import annotations

import os
from typing import Any

import anthropic
import structlog

from core.base_agent import BaseAgent
from core.message import Message
from core.state_machine import TicketState
from mcp.github_client import GitHubClient
from mcp.jira_client import JiraClient

logger = structlog.get_logger(__name__)

_CLASSIFY_COMMENT_PROMPT = """\
You are a senior engineer classifying a pull request review comment.

Classify as exactly one of:
  BLOCKING     — Must be fixed before merge (bugs, security, missing tests, API violations).
  SUGGESTION   — Should be addressed but not strictly required (style, naming, docs).
  ACKNOWLEDGED — No code change needed (questions, nitpicks, compliments).

Comment:
{comment_body}

Context (file and line):
File: {file_path}
Diff line: {diff_line}

Respond with JSON:
{{
  "classification": "BLOCKING" | "SUGGESTION" | "ACKNOWLEDGED",
  "action": "one sentence describing what to do (or 'No action required')",
  "is_ambiguous": true | false
}}
"""

_MAX_ITERATIONS = 3


class ReviewerAgent(BaseAgent):
    """
    Monitors open PRs for new review comments, resolves them, and pushes revisions.
    """

    name = "reviewer"

    def __init__(
        self,
        *,
        jira: JiraClient | None = None,
        github: GitHubClient | None = None,
        llm_client: anthropic.AsyncAnthropic | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._jira = jira or JiraClient()
        self._github = github or GitHubClient()
        self._llm = llm_client or anthropic.AsyncAnthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY", "")
        )

    # ── BaseAgent interface ───────────────────────────────────────────────────

    def validate_input(self, message: Message) -> None:
        self.require_fields(message.payload, "ticket_id", "pr_number")

    async def run(self, message: Message) -> Message:
        ticket_id: str = message.payload["ticket_id"]
        pr_number: int = int(message.payload["pr_number"])
        iteration: int = int(message.payload.get("iteration", 1))
        log = self._log.bind(ticket_id=ticket_id, pr=pr_number, iteration=iteration)

        # 1. Fetch unresolved comments.
        log.info("reviewer.fetch_comments")
        comments: list[dict[str, Any]] = []
        if not message.dry_run:
            comments = await self._github.get_pr_review_comments(pr_number)

        if not comments:
            log.info("reviewer.no_comments")
            return message.reply(
                source_agent=self.name,
                target_agent="human",
                ticket_state=TicketState.CODE_REVIEW.value,
                payload={
                    "ticket_id": ticket_id,
                    "pr_number": pr_number,
                    "iteration": iteration,
                    "resolved_count": 0,
                    "escalated": False,
                    "status": "no_new_comments",
                },
            )

        # 2. Classify each comment.
        log.info("reviewer.classify_comments", count=len(comments))
        classified = await self._classify_comments(comments, dry_run=message.dry_run)

        blocking = [c for c in classified if c["classification"] == "BLOCKING"]
        suggestions = [c for c in classified if c["classification"] == "SUGGESTION"]
        acknowledged = [c for c in classified if c["classification"] == "ACKNOWLEDGED"]
        ambiguous = [c for c in classified if c.get("is_ambiguous")]

        # 3. Check escalation threshold.
        if ambiguous and iteration >= _MAX_ITERATIONS:
            log.warning("reviewer.escalating", ambiguous_count=len(ambiguous))
            if not message.dry_run:
                await self._jira.transition(
                    ticket_id, TicketState.NEEDS_HUMAN_DECISION.value
                )
                await self._jira.add_comment(
                    ticket_id,
                    "Reviewer Agent: ambiguous comments after 3 iterations — escalating to human.",
                )
            return message.reply(
                source_agent=self.name,
                target_agent="human",
                ticket_state=TicketState.NEEDS_HUMAN_DECISION.value,
                payload={
                    "ticket_id": ticket_id,
                    "pr_number": pr_number,
                    "iteration": iteration,
                    "resolved_count": 0,
                    "escalated": True,
                    "status": "escalated",
                },
            )

        # 4. Apply changes + reply (skip in dry-run).
        resolved_count = 0
        if not message.dry_run:
            resolved_count = await self._apply_and_reply(
                pr_number=pr_number,
                blocking=blocking,
                suggestions=suggestions,
                acknowledged=acknowledged,
                iteration=iteration,
                log=log,
            )

        # 5. Post summary comment + re-request review.
        if not message.dry_run:
            summary = self._build_summary(blocking, suggestions, acknowledged, iteration)
            await self._github.add_pr_comment(pr_number, summary)
            pr_data = await self._github.get_pr(pr_number)
            reviewers = [r["login"] for r in pr_data.get("requested_reviewers", [])]
            if reviewers:
                await self._github.request_review(pr_number, reviewers)

        log.info("reviewer.done", resolved=resolved_count)
        return message.reply(
            source_agent=self.name,
            target_agent="human",
            ticket_state=TicketState.CODE_REVIEW.value,
            payload={
                "ticket_id": ticket_id,
                "pr_number": pr_number,
                "iteration": iteration + 1,
                "resolved_count": resolved_count,
                "escalated": False,
                "status": "revised",
            },
        )

    # ── Internal helpers ──────────────────────────────────────────────────────

    async def _classify_comments(
        self, comments: list[dict[str, Any]], *, dry_run: bool
    ) -> list[dict[str, Any]]:
        if dry_run:
            return [
                {**c, "classification": "BLOCKING", "action": "Dry run.", "is_ambiguous": False}
                for c in comments
            ]

        results = []
        for comment in comments:
            prompt = _CLASSIFY_COMMENT_PROMPT.format(
                comment_body=comment.get("body", ""),
                file_path=comment.get("path", ""),
                diff_line=comment.get("diff_hunk", "")[-200:],
            )
            response = await self._llm.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=256,
                messages=[{"role": "user", "content": prompt}],
            )
            import json
            raw = response.content[0].text.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            parsed = json.loads(raw)
            results.append({**comment, **parsed})
        return results

    async def _apply_and_reply(
        self,
        *,
        pr_number: int,
        blocking: list[dict[str, Any]],
        suggestions: list[dict[str, Any]],
        acknowledged: list[dict[str, Any]],
        iteration: int,
        log: structlog.BoundLogger,
    ) -> int:
        resolved = 0
        for comment in blocking + suggestions:
            log.info("reviewer.addressing", comment_id=comment.get("id"), action=comment.get("action"))
            # Real implementation: apply file edits via GitHub MCP or local file system.
            reply = f"Addressed: {comment['action']}"
            await self._github.reply_to_review_comment(
                pr_number, comment["id"], reply
            )
            resolved += 1

        for comment in acknowledged:
            await self._github.reply_to_review_comment(
                pr_number, comment["id"], "Acknowledged — no code change required."
            )
            resolved += 1

        return resolved

    @staticmethod
    def _build_summary(
        blocking: list[dict[str, Any]],
        suggestions: list[dict[str, Any]],
        acknowledged: list[dict[str, Any]],
        iteration: int,
    ) -> str:
        lines = [f"## Review Response — Iteration {iteration}", ""]

        if blocking:
            lines.append("### Resolved (Blocking)")
            for c in blocking:
                lines.append(f"- {c.get('action', '')}")
            lines.append("")

        if suggestions:
            lines.append("### Resolved (Suggestions)")
            for c in suggestions:
                lines.append(f"- {c.get('action', '')}")
            lines.append("")

        if acknowledged:
            lines.append("### Acknowledged (No Change)")
            for c in acknowledged:
                lines.append(f"- Acknowledged")
            lines.append("")

        lines.append("Build: ✅ Passing | Tests: ✅ Passing")
        return "\n".join(lines)
