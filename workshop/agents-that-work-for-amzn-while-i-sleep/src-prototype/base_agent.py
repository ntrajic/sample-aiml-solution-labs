"""
core/base_agent.py
Abstract base class that every agent must extend.
"""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any

import structlog

from core.message import Message

logger = structlog.get_logger(__name__)


class AgentError(Exception):
    """Base exception for agent-level failures."""


class InputValidationError(AgentError):
    """Raised when a message payload does not satisfy the agent's input schema."""


class BaseAgent(ABC):
    """
    Contract every agent must fulfil.

    Subclasses implement :meth:`run` and :meth:`validate_input`.
    The base class provides logging, timing, and dry-run enforcement.
    """

    #: Logical name used in routing and logs.  Override in each subclass.
    name: str = "base"

    def __init__(self, *, config: dict[str, Any] | None = None) -> None:
        self.config: dict[str, Any] = config or {}
        self._log = logger.bind(agent=self.name)

    # ── Public interface ──────────────────────────────────────────────────────

    async def process(self, message: Message) -> Message:
        """
        Entry point called by the SOP Engine.

        Validates the input, delegates to :meth:`run`, and logs timing.
        Never raises — on error it returns a message with ``error`` in the payload.
        """
        self._log.info(
            "agent.start",
            ticket_id=message.ticket_id,
            msg_id=message.id,
            dry_run=message.dry_run,
        )
        start = time.monotonic()

        try:
            self.validate_input(message)
            result = await self.run(message)
        except InputValidationError as exc:
            self._log.warning("agent.input_invalid", error=str(exc))
            return message.reply(
                source_agent=self.name,
                target_agent="human",
                payload={"error": str(exc), "escalate": True},
            )
        except Exception as exc:  # noqa: BLE001
            self._log.exception("agent.error", error=str(exc))
            return message.reply(
                source_agent=self.name,
                target_agent="human",
                payload={"error": str(exc), "escalate": True},
            )
        finally:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            self._log.info("agent.done", elapsed_ms=elapsed_ms)

        return result

    @abstractmethod
    async def run(self, message: Message) -> Message:
        """
        Core agent logic.

        Consume *message*, perform work (or simulate in dry-run mode), and
        return a new Message directed at the next agent or human gate.

        Must be idempotent: invoking twice with the same input produces
        the same output and does not create duplicate side effects.
        """

    @abstractmethod
    def validate_input(self, message: Message) -> None:
        """
        Assert that *message.payload* contains the fields this agent needs.

        Raises:
            InputValidationError: if a required field is missing or invalid.
        """

    # ── Helpers for subclasses ────────────────────────────────────────────────

    def require_fields(self, payload: dict[str, Any], *fields: str) -> None:
        """Assert that all *fields* are present and non-empty in *payload*."""
        missing = [f for f in fields if not payload.get(f)]
        if missing:
            raise InputValidationError(
                f"[{self.name}] Missing required payload fields: {missing}"
            )

    def is_dry_run(self, message: Message) -> bool:
        """Convenience accessor."""
        return message.dry_run

    def log(self) -> structlog.BoundLogger:  # pragma: no cover
        return self._log
