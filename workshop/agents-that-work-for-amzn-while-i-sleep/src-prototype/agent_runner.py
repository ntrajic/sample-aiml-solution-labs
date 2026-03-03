"""
orchestration/agent_runner.py
Agent runner — executes agents sequentially or in parallel with structured logging.
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any

import structlog

from core.base_agent import BaseAgent
from core.message import Message

logger = structlog.get_logger(__name__)


@dataclass
class RunResult:
    """Result of a single agent execution."""

    agent_name: str
    ticket_id: str
    success: bool
    output: Message | None = None
    error: str = ""
    duration_ms: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class AgentRunner:
    """
    Executes one or more agents and collects structured results.

    Supports:
    - Sequential execution (one after another).
    - Parallel execution (concurrent tasks, bounded by a semaphore).
    - Timeout enforcement per agent.
    """

    def __init__(
        self,
        *,
        max_concurrency: int = 5,
        timeout_seconds: float = 600.0,
    ) -> None:
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._timeout = timeout_seconds
        self._log = logger.bind(runner="AgentRunner")

    # ── Public API ────────────────────────────────────────────────────────────

    async def run_sequential(
        self, steps: list[tuple[BaseAgent, Message]]
    ) -> list[RunResult]:
        """
        Execute *steps* one by one, passing each output as context to the next.
        Returns a result for each step.
        """
        results: list[RunResult] = []
        for agent, message in steps:
            result = await self._execute(agent, message)
            results.append(result)
            if not result.success:
                self._log.warning(
                    "runner.sequential.halted",
                    agent=agent.name,
                    error=result.error,
                )
                break
        return results

    async def run_parallel(
        self, tasks: list[tuple[BaseAgent, Message]]
    ) -> list[RunResult]:
        """
        Execute *tasks* concurrently (up to *max_concurrency* at a time).
        Returns results in completion order (not submission order).
        """
        async def bounded(agent: BaseAgent, message: Message) -> RunResult:
            async with self._semaphore:
                return await self._execute(agent, message)

        coroutines = [bounded(agent, msg) for agent, msg in tasks]
        results = await asyncio.gather(*coroutines, return_exceptions=False)
        return list(results)

    async def run_single(self, agent: BaseAgent, message: Message) -> RunResult:
        """Execute a single agent with timeout and logging."""
        return await self._execute(agent, message)

    # ── Internal ──────────────────────────────────────────────────────────────

    async def _execute(self, agent: BaseAgent, message: Message) -> RunResult:
        log = self._log.bind(agent=agent.name, ticket_id=message.ticket_id)
        log.info("runner.execute.start")
        start = time.monotonic()

        try:
            output = await asyncio.wait_for(
                agent.process(message), timeout=self._timeout
            )
            duration_ms = int((time.monotonic() - start) * 1000)
            log.info("runner.execute.success", duration_ms=duration_ms)
            return RunResult(
                agent_name=agent.name,
                ticket_id=message.ticket_id,
                success=True,
                output=output,
                duration_ms=duration_ms,
            )

        except asyncio.TimeoutError:
            duration_ms = int((time.monotonic() - start) * 1000)
            error = f"Agent {agent.name!r} timed out after {self._timeout}s"
            log.error("runner.execute.timeout", duration_ms=duration_ms)
            return RunResult(
                agent_name=agent.name,
                ticket_id=message.ticket_id,
                success=False,
                error=error,
                duration_ms=duration_ms,
            )

        except Exception as exc:  # noqa: BLE001
            duration_ms = int((time.monotonic() - start) * 1000)
            log.exception("runner.execute.error", error=str(exc))
            return RunResult(
                agent_name=agent.name,
                ticket_id=message.ticket_id,
                success=False,
                error=str(exc),
                duration_ms=duration_ms,
            )

    def summarise(self, results: list[RunResult]) -> dict[str, Any]:
        """Return a summary dict suitable for structured logging."""
        return {
            "total": len(results),
            "success": sum(1 for r in results if r.success),
            "failed": sum(1 for r in results if not r.success),
            "total_ms": sum(r.duration_ms for r in results),
            "errors": [
                {"agent": r.agent_name, "ticket": r.ticket_id, "error": r.error}
                for r in results
                if not r.success
            ],
        }
