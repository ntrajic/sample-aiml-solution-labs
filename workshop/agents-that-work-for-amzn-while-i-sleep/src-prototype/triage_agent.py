"""
agents/triage_agent.py
Triage Agent — classifies JIRA tickets and routes them to the correct next state.
"""
from __future__ import annotations

import os
from typing import Any

import anthropic
import structlog

from core.base_agent import BaseAgent, InputValidationError
from core.message import Message
from core.state_machine import TicketState
from mcp.jira_client import JiraClient

logger = structlog.get_logger(__name__)

_CLASSIFICATION_PROMPT = """\
You are a senior software engineer triaging a JIRA ticket. Your job is to classify
the ticket into exactly one of these categories:

READY        — Clear description, explicit acceptance criteria, scope ≤ 3 files.
NEEDS_INFO   — Vague description, missing criteria, unresolved dependencies.
COMPLEX      — Multiple viable approaches with non-trivial trade-offs.
OUT_OF_SCOPE — Production deploy decision, security-sensitive, or architectural redesign.

Respond with a JSON object containing:
  "classification": one of READY / NEEDS_INFO / COMPLEX / OUT_OF_SCOPE
  "rationale": one paragraph explaining the decision
  "clarifications": list of questions (empty unless NEEDS_INFO)
  "complexity_note": brief note (empty unless COMPLEX)

Ticket ID: {ticket_id}
Title: {title}
Description:
{description}

Acceptance Criteria:
{acceptance_criteria}
"""


class TriageAgent(BaseAgent):
    """
    Reads backlog tickets, classifies them, posts JIRA comments, and transitions
    ticket state so the Developer Agent can pick up `READY` items.
    """

    name = "triage"

    def __init__(
        self,
        *,
        jira: JiraClient | None = None,
        llm_client: anthropic.AsyncAnthropic | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._jira = jira or JiraClient()
        self._llm = llm_client or anthropic.AsyncAnthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY", "")
        )

    # ── BaseAgent interface ───────────────────────────────────────────────────

    def validate_input(self, message: Message) -> None:
        self.require_fields(message.payload, "ticket_id")

    async def run(self, message: Message) -> Message:
        ticket_id: str = message.payload["ticket_id"]
        log = self._log.bind(ticket_id=ticket_id)

        # 1. Fetch full ticket details.
        log.info("triage.fetch_ticket")
        ticket_data = await self._jira.get_ticket(ticket_id)
        fields = ticket_data.get("fields", {})
        title: str = fields.get("summary", "")
        description: str = fields.get("description", "") or ""
        acceptance_criteria: str = fields.get("acceptance_criteria", "") or ""

        # 2. Classify via LLM.
        log.info("triage.classify")
        classification_result = await self._classify(
            ticket_id=ticket_id,
            title=title,
            description=description,
            acceptance_criteria=acceptance_criteria,
            dry_run=message.dry_run,
        )

        classification: str = classification_result["classification"]
        rationale: str = classification_result["rationale"]
        clarifications: list[str] = classification_result.get("clarifications", [])
        complexity_note: str = classification_result.get("complexity_note", "")

        log.info("triage.classified", classification=classification)

        # 3. Post comment and transition ticket (skip in dry-run).
        comment_id = ""
        new_state = ""

        if not message.dry_run:
            comment_body = self._format_comment(
                classification, rationale, clarifications, complexity_note
            )
            comment_result = await self._jira.add_comment(ticket_id, comment_body)
            comment_id = comment_result.get("id", "")

            target_state = self._target_state(classification)
            await self._jira.transition(ticket_id, target_state)
            new_state = target_state

        # 4. Build and return output message.
        target_agent = self._next_agent(classification)
        return message.reply(
            source_agent=self.name,
            target_agent=target_agent,
            ticket_state=self._target_state(classification),
            payload={
                "ticket_id": ticket_id,
                "classification": classification,
                "rationale": rationale,
                "clarifications": clarifications,
                "complexity_note": complexity_note,
                "jira_comment_id": comment_id,
                "new_state": new_state,
            },
        )

    # ── Internal helpers ──────────────────────────────────────────────────────

    async def _classify(
        self,
        *,
        ticket_id: str,
        title: str,
        description: str,
        acceptance_criteria: str,
        dry_run: bool,
    ) -> dict[str, Any]:
        if dry_run:
            return {
                "classification": "READY",
                "rationale": "Dry run — classification skipped.",
                "clarifications": [],
                "complexity_note": "",
            }

        prompt = _CLASSIFICATION_PROMPT.format(
            ticket_id=ticket_id,
            title=title,
            description=description,
            acceptance_criteria=acceptance_criteria or "Not provided.",
        )

        response = await self._llm.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        import json
        raw = response.content[0].text.strip()
        # Strip possible markdown code fences.
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw)

    @staticmethod
    def _target_state(classification: str) -> str:
        mapping = {
            "READY": TicketState.READY_FOR_DEV.value,
            "NEEDS_INFO": TicketState.NEEDS_INFO.value,
            "COMPLEX": TicketState.RESEARCH_NEEDED.value,
            "OUT_OF_SCOPE": TicketState.OUT_OF_SCOPE.value,
        }
        return mapping.get(classification, TicketState.NEEDS_INFO.value)

    @staticmethod
    def _next_agent(classification: str) -> str:
        mapping = {
            "READY": "developer",
            "NEEDS_INFO": "human",
            "COMPLEX": "researcher",
            "OUT_OF_SCOPE": "human",
        }
        return mapping.get(classification, "human")

    @staticmethod
    def _format_comment(
        classification: str,
        rationale: str,
        clarifications: list[str],
        complexity_note: str,
    ) -> str:
        emoji = {
            "READY": "✅",
            "NEEDS_INFO": "❓",
            "COMPLEX": "🔬",
            "OUT_OF_SCOPE": "🚫",
        }.get(classification, "🤖")

        lines = [
            f"{emoji} **Triage Agent — Classification: {classification}**",
            "",
            rationale,
        ]

        if clarifications:
            lines += ["", "**Clarifications needed:**"]
            for i, q in enumerate(clarifications, 1):
                lines.append(f"{i}. {q}")
            lines.append("")
            lines.append(
                "_Please update the ticket with the above information and it will be re-triaged automatically._"
            )

        if complexity_note:
            lines += ["", f"**Complexity note:** {complexity_note}"]

        return "\n".join(lines)
