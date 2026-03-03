"""
core/message.py
Immutable message dataclass passed between agents on the message bus.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class Message:
    """
    The canonical unit of communication between agents.

    All fields are immutable once created.  Agents produce a *new* Message
    as their output rather than mutating the input.
    """

    # ── Identity ─────────────────────────────────────────────────────────────
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    """Unique message identifier (UUID4)."""

    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    """
    Links all messages that belong to the same ticket processing chain.
    The first message in a chain sets this; subsequent messages inherit it.
    """

    # ── Routing ───────────────────────────────────────────────────────────────
    source_agent: str = ""
    """Logical name of the agent that produced this message, e.g. 'triage'."""

    target_agent: str = ""
    """Logical name of the agent that should consume this message, e.g. 'developer'."""

    # ── Business context ──────────────────────────────────────────────────────
    ticket_id: str = ""
    """JIRA ticket identifier, e.g. 'PROJ-123'."""

    ticket_state: str = ""
    """Current JIRA ticket state at the time this message was emitted."""

    # ── Payload ───────────────────────────────────────────────────────────────
    payload: dict[str, Any] = field(default_factory=dict)
    """
    Agent-specific structured data.  The SOP Engine validates this against
    the step's input/output schema before forwarding.
    """

    # ── Metadata ──────────────────────────────────────────────────────────────
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    """UTC timestamp at which this message was created."""

    dry_run: bool = False
    """When True, the receiving agent must not produce side effects."""

    # ── Helpers ───────────────────────────────────────────────────────────────

    def reply(
        self,
        *,
        source_agent: str,
        target_agent: str,
        ticket_state: str = "",
        payload: dict[str, Any] | None = None,
        dry_run: bool | None = None,
    ) -> Message:
        """
        Produce a new Message that is a logical reply to this one.

        The ``correlation_id`` is inherited so the full chain can be traced.
        """
        return Message(
            correlation_id=self.correlation_id,
            source_agent=source_agent,
            target_agent=target_agent,
            ticket_id=self.ticket_id,
            ticket_state=ticket_state or self.ticket_state,
            payload=payload or {},
            dry_run=dry_run if dry_run is not None else self.dry_run,
        )

    def to_log_dict(self) -> dict[str, Any]:
        """Serialise to a flat dict suitable for structured logging."""
        return {
            "msg_id": self.id,
            "correlation_id": self.correlation_id,
            "source": self.source_agent,
            "target": self.target_agent,
            "ticket_id": self.ticket_id,
            "ticket_state": self.ticket_state,
            "ts": self.timestamp.isoformat(),
            "dry_run": self.dry_run,
        }

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"Message(id={self.id!r}, "
            f"{self.source_agent!r}→{self.target_agent!r}, "
            f"ticket={self.ticket_id!r}, "
            f"state={self.ticket_state!r})"
        )
