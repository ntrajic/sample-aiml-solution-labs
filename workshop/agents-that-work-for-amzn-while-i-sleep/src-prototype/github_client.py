"""
mcp/github_client.py
GitHub MCP client — wraps all GitHub operations used by the agents.
"""
from __future__ import annotations

import os
from typing import Any

from mcp.base_client import BaseMCPClient


class GitHubClient(BaseMCPClient):
    """
    Thin wrapper around the GitHub MCP server.

    Configuration is loaded from environment variables:

        GITHUB_BASE_URL   — MCP server URL (default: https://api.github.com/mcp)
        GITHUB_TOKEN      — Personal access token or GitHub App token
        GITHUB_REPO       — owner/repo, e.g. acme/backend
    """

    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault(
            "base_url", os.environ.get("GITHUB_BASE_URL", "https://api.github.com/mcp")
        )
        kwargs.setdefault("token", os.environ["GITHUB_TOKEN"])
        self.repo = os.environ.get("GITHUB_REPO", "")
        super().__init__(**kwargs)

    def _auth_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"token {self._token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    # ── Branch operations ─────────────────────────────────────────────────────

    async def create_branch(self, branch_name: str, base: str = "main") -> dict[str, Any]:
        """Create *branch_name* from the HEAD of *base*."""
        return await self.call(
            "github_create_branch",
            {"repo": self.repo, "branch": branch_name, "base": base},
        )

    async def push_commit(
        self,
        branch_name: str,
        message: str,
        files: list[dict[str, str]],
    ) -> dict[str, Any]:
        """
        Commit *files* to *branch_name*.

        Each entry in *files* must have keys ``path`` and ``content``.
        """
        return await self.call(
            "github_push_files",
            {"repo": self.repo, "branch": branch_name, "message": message, "files": files},
        )

    # ── Pull Request operations ───────────────────────────────────────────────

    async def create_pr(
        self,
        *,
        title: str,
        body: str,
        head: str,
        base: str = "main",
        draft: bool = False,
    ) -> dict[str, Any]:
        """Open a Pull Request."""
        return await self.call(
            "github_create_pull_request",
            {
                "repo": self.repo,
                "title": title,
                "body": body,
                "head": head,
                "base": base,
                "draft": draft,
            },
        )

    async def get_pr(self, pr_number: int) -> dict[str, Any]:
        """Fetch PR metadata."""
        return await self.call(
            "github_get_pull_request",
            {"repo": self.repo, "pull_number": pr_number},
        )

    async def list_open_prs(self) -> list[dict[str, Any]]:
        """Return all open PRs for the configured repo."""
        result = await self.call(
            "github_list_pull_requests",
            {"repo": self.repo, "state": "open"},
        )
        return result.get("pull_requests", [])  # type: ignore[return-value]

    async def get_pr_review_comments(self, pr_number: int) -> list[dict[str, Any]]:
        """Return all review comments (line-level) on a PR."""
        result = await self.call(
            "github_list_review_comments",
            {"repo": self.repo, "pull_number": pr_number},
        )
        return result.get("comments", [])  # type: ignore[return-value]

    async def get_pr_comments(self, pr_number: int) -> list[dict[str, Any]]:
        """Return top-level (issue-style) comments on a PR."""
        result = await self.call(
            "github_list_issue_comments",
            {"repo": self.repo, "issue_number": pr_number},
        )
        return result.get("comments", [])  # type: ignore[return-value]

    async def add_pr_comment(self, pr_number: int, body: str) -> dict[str, Any]:
        """Post a top-level comment on a PR."""
        return await self.call(
            "github_create_issue_comment",
            {"repo": self.repo, "issue_number": pr_number, "body": body},
        )

    async def reply_to_review_comment(
        self, pr_number: int, comment_id: int, body: str
    ) -> dict[str, Any]:
        """Reply to an existing line-level review comment."""
        return await self.call(
            "github_reply_to_review_comment",
            {
                "repo": self.repo,
                "pull_number": pr_number,
                "comment_id": comment_id,
                "body": body,
            },
        )

    async def request_review(
        self, pr_number: int, reviewers: list[str]
    ) -> dict[str, Any]:
        """Re-request review from *reviewers*."""
        return await self.call(
            "github_request_reviewers",
            {"repo": self.repo, "pull_number": pr_number, "reviewers": reviewers},
        )

    async def resolve_review_thread(
        self, pr_number: int, thread_id: str
    ) -> dict[str, Any]:
        """Mark a review thread as resolved."""
        return await self.call(
            "github_resolve_review_thread",
            {"repo": self.repo, "pull_number": pr_number, "thread_id": thread_id},
        )
