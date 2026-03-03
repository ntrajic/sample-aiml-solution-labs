"""
mcp/base_client.py
Base MCP client with retry logic and exponential back-off.
"""
from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import Any

import httpx
import structlog

logger = structlog.get_logger(__name__)

#: Default retry settings (overridable per-subclass).
MAX_RETRIES: int = 3
BACKOFF_BASE: float = 2.0  # seconds


class MCPError(Exception):
    """Raised when an MCP tool call fails after all retries."""

    def __init__(self, tool: str, status_code: int | None, detail: str) -> None:
        super().__init__(f"MCP tool {tool!r} failed (HTTP {status_code}): {detail}")
        self.tool = tool
        self.status_code = status_code
        self.detail = detail


class BaseMCPClient(ABC):
    """
    Abstract MCP client.

    Subclasses implement :meth:`_base_url` and optionally override
    :meth:`_auth_headers`.  All tool calls go through :meth:`call`
    which provides retry + exponential back-off.
    """

    def __init__(
        self,
        *,
        base_url: str,
        token: str,
        max_retries: int = MAX_RETRIES,
        backoff_base: float = BACKOFF_BASE,
        dry_run: bool = False,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._token = token
        self._max_retries = max_retries
        self._backoff_base = backoff_base
        self._dry_run = dry_run
        self._log = logger.bind(client=self.__class__.__name__)

        # Allow injection of a mock client in tests.
        self._http: httpx.AsyncClient = http_client or httpx.AsyncClient(
            timeout=30.0,
            headers=self._auth_headers(),
        )

    # ── Public interface ──────────────────────────────────────────────────────

    async def call(self, tool: str, params: dict[str, Any]) -> dict[str, Any]:
        """
        Invoke *tool* with *params*.

        Retries on transient HTTP errors (429, 5xx) with exponential back-off.
        Returns the parsed JSON response body.

        Raises:
            MCPError: after exhausting all retries.
        """
        if self._dry_run:
            self._log.debug("mcp.dry_run", tool=tool, params=params)
            return {"dry_run": True, "tool": tool, "params": params}

        url = f"{self._base_url}/{tool}"
        last_exc: Exception | None = None

        for attempt in range(1, self._max_retries + 1):
            try:
                response = await self._http.post(url, json=params)

                if response.status_code in {429, 500, 502, 503, 504}:
                    wait = self._backoff_base ** attempt
                    self._log.warning(
                        "mcp.retry",
                        tool=tool,
                        attempt=attempt,
                        status=response.status_code,
                        wait_s=wait,
                    )
                    await asyncio.sleep(wait)
                    continue

                response.raise_for_status()
                return response.json()  # type: ignore[no-any-return]

            except httpx.TimeoutException as exc:
                wait = self._backoff_base ** attempt
                self._log.warning(
                    "mcp.timeout", tool=tool, attempt=attempt, wait_s=wait
                )
                last_exc = exc
                await asyncio.sleep(wait)

            except httpx.HTTPStatusError as exc:
                # Non-retryable client errors (4xx except 429).
                raise MCPError(tool, exc.response.status_code, exc.response.text) from exc

        raise MCPError(tool, None, f"Exhausted {self._max_retries} retries") from last_exc

    async def close(self) -> None:
        """Release the underlying HTTP client."""
        await self._http.aclose()

    async def __aenter__(self) -> "BaseMCPClient":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    # ── Subclass hooks ────────────────────────────────────────────────────────

    @abstractmethod
    def _auth_headers(self) -> dict[str, str]:
        """Return the authentication headers for this MCP provider."""
