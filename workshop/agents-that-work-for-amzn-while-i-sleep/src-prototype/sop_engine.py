"""
orchestration/sop_engine.py
SOP Engine — loads the YAML SOP, validates hand-offs, and routes messages between agents.
"""
from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any

import structlog
import yaml

from agents.developer_agent import DeveloperAgent
from agents.researcher_agent import ResearcherAgent
from agents.reviewer_agent import ReviewerAgent
from agents.triage_agent import TriageAgent
from core.base_agent import BaseAgent
from core.message import Message
from mcp.jira_client import JiraClient

logger = structlog.get_logger(__name__)

_DEFAULT_SOP_PATH = Path(__file__).parent.parent.parent / "config" / "SOP.yaml"

# Registry mapping logical agent names → classes.
_AGENT_REGISTRY: dict[str, type[BaseAgent]] = {
    "triage": TriageAgent,
    "developer": DeveloperAgent,
    "reviewer": ReviewerAgent,
    "researcher": ResearcherAgent,
}


class HandOffValidationError(Exception):
    """Raised when an agent output does not satisfy the next step's input schema."""


class SOPEngine:
    """
    Interprets the SOP YAML and drives the multi-agent workflow.

    Usage::

        engine = SOPEngine()
        engine.load()
        await engine.run_triage_cycle()
        await engine.run_review_cycle()
    """

    def __init__(
        self,
        *,
        sop_path: Path | None = None,
        jira: JiraClient | None = None,
        dry_run: bool = False,
        agent_overrides: dict[str, BaseAgent] | None = None,
    ) -> None:
        self._sop_path = sop_path or Path(
            os.environ.get("SOP_CONFIG_PATH", str(_DEFAULT_SOP_PATH))
        )
        self._jira = jira or JiraClient()
        self._dry_run = dry_run or bool(os.environ.get("AGENT_DRY_RUN"))
        self._sop: dict[str, Any] = {}
        self._agents: dict[str, BaseAgent] = agent_overrides or {}
        self._log = logger.bind(engine="SOPEngine")

    # ── Public API ────────────────────────────────────────────────────────────

    def load(self) -> None:
        """Parse the SOP YAML file."""
        self._log.info("sop.load", path=str(self._sop_path))
        with self._sop_path.open() as fh:
            self._sop = yaml.safe_load(fh)
        self._log.info("sop.loaded", version=self._sop.get("sop", {}).get("version"))

    async def run_triage_cycle(self, *, ticket_id: str | None = None) -> list[Message]:
        """
        Execute one triage cycle.

        If *ticket_id* is provided, process only that ticket.
        Otherwise query the JIRA backlog.
        """
        self._log.info("cycle.triage.start")
        ticket_ids = [ticket_id] if ticket_id else await self._fetch_backlog_ids()

        results: list[Message] = []
        tasks = [self._process_ticket(tid) for tid in ticket_ids]
        for coro in asyncio.as_completed(tasks):
            result = await coro
            results.append(result)
        self._log.info("cycle.triage.done", processed=len(results))
        return results

    async def run_review_cycle(self) -> list[Message]:
        """
        Execute one review cycle — address all open PRs with unresolved comments.
        """
        self._log.info("cycle.review.start")
        if self._dry_run:
            return []

        prs_with_comments = await self._fetch_prs_with_comments()
        results: list[Message] = []

        for pr in prs_with_comments:
            msg = Message(
                source_agent="sop_engine",
                target_agent="reviewer",
                ticket_id=pr.get("ticket_id", ""),
                ticket_state="Code Review",
                payload={"ticket_id": pr.get("ticket_id", ""), "pr_number": pr["number"]},
                dry_run=self._dry_run,
            )
            result = await self._get_agent("reviewer").process(msg)
            results.append(result)

        self._log.info("cycle.review.done", processed=len(results))
        return results

    # ── Internal ──────────────────────────────────────────────────────────────

    async def _process_ticket(self, ticket_id: str) -> Message:
        """Drive a single ticket through the SOP from triage onward."""
        log = self._log.bind(ticket_id=ticket_id)

        # Step 1: Triage.
        triage_msg = Message(
            source_agent="sop_engine",
            target_agent="triage",
            ticket_id=ticket_id,
            ticket_state="Backlog",
            payload={"ticket_id": ticket_id},
            dry_run=self._dry_run,
        )
        triage_result = await self._get_agent("triage").process(triage_msg)
        log.info("sop.triage_done", classification=triage_result.payload.get("classification"))

        classification = triage_result.payload.get("classification", "NEEDS_INFO")

        # Step 2: Route based on classification.
        if classification == "READY":
            return await self._get_agent("developer").process(
                triage_result.reply(
                    source_agent="sop_engine",
                    target_agent="developer",
                    ticket_state="Ready for Dev",
                    payload={**triage_result.payload},
                )
            )

        if classification == "COMPLEX":
            return await self._get_agent("researcher").process(
                triage_result.reply(
                    source_agent="sop_engine",
                    target_agent="researcher",
                    ticket_state="Research Needed",
                    payload={**triage_result.payload},
                )
            )

        # NEEDS_INFO / OUT_OF_SCOPE → human gate (return as-is).
        return triage_result

    async def _fetch_backlog_ids(self) -> list[str]:
        if self._dry_run:
            return []
        tickets = await self._jira.query_backlog()
        return [t["key"] for t in tickets]

    async def _fetch_prs_with_comments(self) -> list[dict[str, Any]]:
        """Return open PRs that have unresolved review comments."""
        from mcp.github_client import GitHubClient
        github = GitHubClient()
        open_prs = await github.get_pr_review_comments.__func__(github, 0)  # type: ignore
        # Simplified: return all open PRs.  Real impl would filter by comment status.
        return await github.list_open_prs()

    def _get_agent(self, name: str) -> BaseAgent:
        if name not in self._agents:
            cls = _AGENT_REGISTRY.get(name)
            if cls is None:
                raise ValueError(f"Unknown agent: {name!r}")
            self._agents[name] = cls(config=self._sop.get("sop", {}).get("agents", {}).get(name, {}))
        return self._agents[name]

    @staticmethod
    def _validate_handoff(
        output: Message, required_fields: list[str], step_name: str
    ) -> None:
        missing = [f for f in required_fields if not output.payload.get(f)]
        if missing:
            raise HandOffValidationError(
                f"Step {step_name!r}: output message missing required fields {missing}"
            )


# ── CLI entry point ───────────────────────────────────────────────────────────

def main() -> None:  # pragma: no cover
    import asyncio
    import click

    @click.command()
    @click.option("--entry", default="triage_cycle", help="Entry point to run.")
    @click.option("--ticket", default=None, help="Process a specific ticket only.")
    @click.option("--dry-run", is_flag=True, default=False)
    @click.option(
        "--sop-path",
        default=None,
        type=click.Path(exists=True, path_type=Path),
    )
    def cli(entry: str, ticket: str | None, dry_run: bool, sop_path: Path | None) -> None:
        engine = SOPEngine(sop_path=sop_path, dry_run=dry_run)
        engine.load()
        if entry == "triage_cycle":
            asyncio.run(engine.run_triage_cycle(ticket_id=ticket))
        elif entry == "review_cycle":
            asyncio.run(engine.run_review_cycle())
        else:
            raise click.UsageError(f"Unknown entry point: {entry!r}")

    cli()
