"""
mcp/jira_client.py
JIRA MCP client — wraps all JIRA operations used by the agents.
"""
from __future__ import annotations

import os
from typing import Any

from mcp.base_client import BaseMCPClient


class JiraClient(BaseMCPClient):
    """
    Thin wrapper around the JIRA MCP server.

    Every method maps to a single MCP tool call.
    Configuration is loaded from environment variables:

        JIRA_BASE_URL       — e.g. https://yourcompany.atlassian.net/mcp
        JIRA_API_TOKEN      — API token
        JIRA_PROJECT_KEY    — Default project key, e.g. PROJ
    """

    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("base_url", os.environ["JIRA_BASE_URL"])
        kwargs.setdefault("token", os.environ["JIRA_API_TOKEN"])
        self.project_key = os.environ.get("JIRA_PROJECT_KEY", "")
        super().__init__(**kwargs)

    def _auth_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

    # ── Ticket queries ────────────────────────────────────────────────────────

    async def get_ticket(self, ticket_id: str) -> dict[str, Any]:
        """Fetch full ticket details by ID."""
        return await self.call("jira_get_issue", {"issue_key": ticket_id})

    async def query_backlog(
        self,
        status: str = "Backlog",
        max_results: int = 50,
    ) -> list[dict[str, Any]]:
        """Return tickets in *status* for the configured project."""
        jql = f'project = "{self.project_key}" AND status = "{status}" ORDER BY created ASC'
        result = await self.call(
            "jira_search",
            {"jql": jql, "maxResults": max_results, "fields": ["summary", "description", "status"]},
        )
        return result.get("issues", [])  # type: ignore[return-value]

    async def query_ready_for_dev(self) -> list[dict[str, Any]]:
        """Convenience: return all tickets in 'Ready for Dev' state."""
        return await self.query_backlog(status="Ready for Dev")

    # ── Ticket mutations ──────────────────────────────────────────────────────

    async def add_comment(self, ticket_id: str, body: str) -> dict[str, Any]:
        """Post *body* as a comment on *ticket_id*."""
        return await self.call(
            "jira_add_comment",
            {"issue_key": ticket_id, "comment": body},
        )

    async def transition(self, ticket_id: str, target_state: str) -> dict[str, Any]:
        """
        Transition *ticket_id* to *target_state*.

        The MCP server resolves the transition ID from the state name.
        """
        return await self.call(
            "jira_transition_issue",
            {"issue_key": ticket_id, "transition_name": target_state},
        )

    async def update_field(
        self, ticket_id: str, field: str, value: Any
    ) -> dict[str, Any]:
        """Update a single custom or standard field on a ticket."""
        return await self.call(
            "jira_update_issue",
            {"issue_key": ticket_id, "fields": {field: value}},
        )

    async def add_label(self, ticket_id: str, label: str) -> dict[str, Any]:
        """Append *label* to the ticket without overwriting existing labels."""
        ticket = await self.get_ticket(ticket_id)
        existing: list[str] = ticket.get("fields", {}).get("labels", [])
        if label not in existing:
            existing.append(label)
        return await self.update_field(ticket_id, "labels", existing)

    async def create_ticket(
        self,
        summary: str,
        description: str,
        issue_type: str = "Bug",
        labels: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create a new ticket in the configured project."""
        return await self.call(
            "jira_create_issue",
            {
                "project_key": self.project_key,
                "summary": summary,
                "description": description,
                "issue_type": issue_type,
                "labels": labels or [],
            },
        )
