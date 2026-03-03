"""
agents/researcher_agent.py
Researcher Agent — explores alternatives for complex tickets and presents options to a human.
"""
from __future__ import annotations

import os
from typing import Any

import anthropic
import structlog

from core.base_agent import BaseAgent
from core.message import Message
from core.state_machine import TicketState
from mcp.jira_client import JiraClient

logger = structlog.get_logger(__name__)

_RESEARCH_PROMPT = """\
You are a staff engineer researching implementation approaches for a complex JIRA ticket.

Ticket ID: {ticket_id}
Title: {title}
Description:
{description}

Constraints: {constraints}
Complexity note: {complexity_note}

Produce between 2 and 5 distinct implementation options. For each option provide:
- option_id: A, B, C, ...
- title: short descriptive name
- description: 2-3 sentences
- pros: list of advantages
- cons: list of disadvantages
- complexity: integer 1-5
- risk: integer 1-5
- estimated_hours: integer
- references: list of doc links or notes

Also provide:
- recommendation: the option_id you would choose
- rationale: why (2-3 sentences, advisory only)

Respond ONLY with valid JSON matching the above schema. No preamble, no markdown fences.
"""


class ResearcherAgent(BaseAgent):
    """
    Researches complex tickets, generates a trade-off analysis, and posts the
    options to JIRA for a human to select before implementation begins.
    """

    name = "researcher"

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
        complexity_note: str = message.payload.get("complexity_note", "")
        constraints: list[str] = message.payload.get("constraints", [])
        log = self._log.bind(ticket_id=ticket_id)

        # 1. Fetch ticket.
        log.info("researcher.fetch_ticket")
        ticket_data = await self._jira.get_ticket(ticket_id)
        fields = ticket_data.get("fields", {})
        title: str = fields.get("summary", "")
        description: str = fields.get("description", "") or ""

        # 2. Research options.
        log.info("researcher.research")
        result = await self._research(
            ticket_id=ticket_id,
            title=title,
            description=description,
            complexity_note=complexity_note,
            constraints=constraints,
            dry_run=message.dry_run,
        )

        options: list[dict[str, Any]] = result.get("options", [])
        recommendation: str = result.get("recommendation", "")
        rationale: str = result.get("rationale", "")

        # Validate minimum 2 options.
        if len(options) < 2 and not message.dry_run:
            log.warning("researcher.insufficient_options", count=len(options))
            await self._jira.add_comment(
                ticket_id,
                "🤖 Researcher Agent: unable to identify at least 2 viable options — "
                "requesting architectural guidance from the team.",
            )
            return message.reply(
                source_agent=self.name,
                target_agent="human",
                ticket_state=TicketState.NEEDS_HUMAN_DECISION.value,
                payload={
                    "ticket_id": ticket_id,
                    "options": options,
                    "recommendation": recommendation,
                    "rationale": rationale,
                    "awaiting_human": True,
                    "jira_comment_id": "",
                },
            )

        # 3. Post options report to JIRA.
        comment_id = ""
        if not message.dry_run:
            comment_body = self._format_report(options, recommendation, rationale)
            comment_result = await self._jira.add_comment(ticket_id, comment_body)
            comment_id = comment_result.get("id", "")
            await self._jira.transition(ticket_id, TicketState.AWAITING_DECISION.value)

        log.info("researcher.done", options=len(options))
        return message.reply(
            source_agent=self.name,
            target_agent="human",
            ticket_state=TicketState.AWAITING_DECISION.value,
            payload={
                "ticket_id": ticket_id,
                "options": options,
                "recommendation": recommendation,
                "rationale": rationale,
                "awaiting_human": True,
                "jira_comment_id": comment_id,
            },
        )

    # ── Internal helpers ──────────────────────────────────────────────────────

    async def _research(
        self,
        *,
        ticket_id: str,
        title: str,
        description: str,
        complexity_note: str,
        constraints: list[str],
        dry_run: bool,
    ) -> dict[str, Any]:
        if dry_run:
            return {
                "options": [
                    {
                        "option_id": "A",
                        "title": "Dry Run Option A",
                        "description": "Dry run.",
                        "pros": ["fast"],
                        "cons": ["not real"],
                        "complexity": 1,
                        "risk": 1,
                        "estimated_hours": 1,
                        "references": [],
                    },
                    {
                        "option_id": "B",
                        "title": "Dry Run Option B",
                        "description": "Dry run.",
                        "pros": ["scalable"],
                        "cons": ["slower"],
                        "complexity": 2,
                        "risk": 2,
                        "estimated_hours": 4,
                        "references": [],
                    },
                ],
                "recommendation": "A",
                "rationale": "Dry run — no real research performed.",
            }

        prompt = _RESEARCH_PROMPT.format(
            ticket_id=ticket_id,
            title=title,
            description=description,
            constraints=", ".join(constraints) or "None specified.",
            complexity_note=complexity_note or "Not provided.",
        )
        response = await self._llm.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        import json
        raw = response.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw)

    @staticmethod
    def _format_report(
        options: list[dict[str, Any]],
        recommendation: str,
        rationale: str,
    ) -> str:
        lines = ["🔬 **Researcher Agent — Options Report**", ""]

        for opt in options:
            oid = opt.get("option_id", "?")
            lines += [
                f"---",
                f"**Option {oid}: {opt.get('title', '')}**",
                f"- Complexity: {opt.get('complexity')}/5 | "
                f"Risk: {opt.get('risk')}/5 | "
                f"Estimate: {opt.get('estimated_hours')}h",
                f"- **Pros:** {', '.join(opt.get('pros', []))}",
                f"- **Cons:** {', '.join(opt.get('cons', []))}",
                f"- *{opt.get('description', '')}*",
            ]
            refs = opt.get("references", [])
            if refs:
                lines.append(f"- References: {', '.join(refs)}")
            lines.append("")

        lines += [
            "---",
            f"**Agent Recommendation: Option {recommendation}** — {rationale}",
            "",
            "_Please reply to this comment with your chosen option (A, B, C…) to proceed._",
        ]
        return "\n".join(lines)
