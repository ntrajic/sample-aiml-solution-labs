"""
core/state_machine.py
Ticket state machine — defines valid states and allowed transitions.
"""
from __future__ import annotations

from enum import Enum


class TicketState(str, Enum):
    """
    All possible states for a JIRA ticket as it flows through the system.

    Inherits from ``str`` so values can be compared directly to JIRA API strings.
    """

    BACKLOG = "Backlog"
    TRIAGE = "Triage"
    NEEDS_INFO = "Waiting for Info"
    READY_FOR_DEV = "Ready for Dev"
    RESEARCH_NEEDED = "Research Needed"
    AWAITING_DECISION = "Awaiting Decision"
    IN_PROGRESS = "In Progress"
    CODE_REVIEW = "Code Review"
    CHANGES_REQUESTED = "Changes Requested"
    APPROVED = "Approved"
    DONE = "Done"
    OUT_OF_SCOPE = "Out of Scope"
    BLOCKED = "Blocked"
    NEEDS_HUMAN_DECISION = "Needs Human Decision"


# Adjacency map: state → set of states it may transition to.
_TRANSITIONS: dict[TicketState, frozenset[TicketState]] = {
    TicketState.BACKLOG: frozenset({
        TicketState.TRIAGE,
    }),
    TicketState.TRIAGE: frozenset({
        TicketState.READY_FOR_DEV,
        TicketState.NEEDS_INFO,
        TicketState.RESEARCH_NEEDED,
        TicketState.OUT_OF_SCOPE,
    }),
    TicketState.NEEDS_INFO: frozenset({
        TicketState.TRIAGE,          # re-triage after human updates ticket
    }),
    TicketState.RESEARCH_NEEDED: frozenset({
        TicketState.AWAITING_DECISION,
    }),
    TicketState.AWAITING_DECISION: frozenset({
        TicketState.READY_FOR_DEV,   # human selects an approach
    }),
    TicketState.READY_FOR_DEV: frozenset({
        TicketState.IN_PROGRESS,
        TicketState.BLOCKED,
    }),
    TicketState.IN_PROGRESS: frozenset({
        TicketState.CODE_REVIEW,
        TicketState.BLOCKED,
    }),
    TicketState.CODE_REVIEW: frozenset({
        TicketState.CHANGES_REQUESTED,
        TicketState.APPROVED,
    }),
    TicketState.CHANGES_REQUESTED: frozenset({
        TicketState.IN_PROGRESS,     # reviewer agent picks up changes
        TicketState.NEEDS_HUMAN_DECISION,
    }),
    TicketState.NEEDS_HUMAN_DECISION: frozenset({
        TicketState.IN_PROGRESS,     # human resolves ambiguity
        TicketState.CODE_REVIEW,
    }),
    TicketState.APPROVED: frozenset({
        TicketState.DONE,
    }),
    TicketState.BLOCKED: frozenset({
        TicketState.READY_FOR_DEV,   # human unblocks
        TicketState.TRIAGE,
    }),
    # Terminal states — no outbound transitions.
    TicketState.DONE: frozenset(),
    TicketState.OUT_OF_SCOPE: frozenset(),
}


class InvalidTransitionError(Exception):
    """Raised when an agent attempts a forbidden state transition."""

    def __init__(self, from_state: TicketState, to_state: TicketState) -> None:
        super().__init__(
            f"Cannot transition from {from_state.value!r} to {to_state.value!r}."
        )
        self.from_state = from_state
        self.to_state = to_state


class StateMachine:
    """Validates and records ticket state transitions."""

    def __init__(self, initial_state: TicketState = TicketState.BACKLOG) -> None:
        self._state = initial_state

    @property
    def state(self) -> TicketState:
        return self._state

    def can_transition(self, to: TicketState) -> bool:
        """Return True if the transition from the current state to *to* is allowed."""
        return to in _TRANSITIONS.get(self._state, frozenset())

    def transition(self, to: TicketState) -> TicketState:
        """
        Advance to *to* and return the new state.

        Raises:
            InvalidTransitionError: if the transition is not allowed.
        """
        if not self.can_transition(to):
            raise InvalidTransitionError(self._state, to)
        self._state = to
        return self._state

    def allowed_transitions(self) -> frozenset[TicketState]:
        """Return all states reachable from the current state."""
        return _TRANSITIONS.get(self._state, frozenset())

    @classmethod
    def from_string(cls, state_str: str) -> "StateMachine":
        """Construct a StateMachine from a raw JIRA state string."""
        return cls(TicketState(state_str))

    def __repr__(self) -> str:  # pragma: no cover
        return f"StateMachine(state={self._state.value!r})"
