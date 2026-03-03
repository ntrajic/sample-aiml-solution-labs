"""
triggers/shell_loop.py
Shell loop (Ralph Wiggum loop) — polls for work and executes the SOP Engine.

Run directly:
    python -m triggers.shell_loop
    python -m triggers.shell_loop --sleep-seconds 30 --dry-run

Or via the CLI entry point:
    agent-loop --sleep-seconds 60
"""
from __future__ import annotations

import asyncio
import json
import os
import signal
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import click
import structlog

logger = structlog.get_logger(__name__)

_DEFAULT_SLEEP = int(os.environ.get("LOOP_SLEEP_SECONDS", "60"))
_SHUTDOWN_REQUESTED = False


def _handle_sigterm(signum: int, frame: Any) -> None:  # noqa: ANN001
    """Set the shutdown flag on SIGTERM so the loop finishes its current task."""
    global _SHUTDOWN_REQUESTED
    logger.info("loop.sigterm_received")
    _SHUTDOWN_REQUESTED = True


signal.signal(signal.SIGTERM, _handle_sigterm)


async def _run_cycle(
    *,
    dry_run: bool,
    ticket_id: str | None,
    entry: str,
    sop_path: Path | None,
) -> dict[str, Any]:
    """Execute one SOP cycle and return a structured result dict."""
    from orchestration.sop_engine import SOPEngine

    engine = SOPEngine(sop_path=sop_path, dry_run=dry_run)
    engine.load()

    if entry == "triage_cycle":
        results = await engine.run_triage_cycle(ticket_id=ticket_id)
    elif entry == "review_cycle":
        results = await engine.run_review_cycle()
    else:
        raise ValueError(f"Unknown entry point: {entry!r}")

    return {
        "entry": entry,
        "processed": len(results),
        "tickets": [r.payload.get("ticket_id", "") for r in results],
    }


async def loop(
    *,
    sleep_seconds: int,
    dry_run: bool,
    ticket_id: str | None,
    entry: str,
    sop_path: Path | None,
    max_iterations: int | None,
) -> None:
    """
    The Ralph Wiggum loop.

    Polls for work, executes the SOP, sleeps, and repeats until SIGTERM or
    *max_iterations* is reached.
    """
    global _SHUTDOWN_REQUESTED
    log = logger.bind(entry=entry, dry_run=dry_run)
    iteration = 0

    log.info("loop.start", sleep_seconds=sleep_seconds)

    while not _SHUTDOWN_REQUESTED:
        iteration += 1
        ts = datetime.now(timezone.utc).isoformat()

        log.info("loop.iteration.start", iteration=iteration, ts=ts)

        try:
            result = await _run_cycle(
                dry_run=dry_run,
                ticket_id=ticket_id,
                entry=entry,
                sop_path=sop_path,
            )
            log_line = {
                "ts": ts,
                "level": "INFO",
                "iteration": iteration,
                "status": "success",
                **result,
            }
        except Exception as exc:  # noqa: BLE001
            log.exception("loop.iteration.error", iteration=iteration, error=str(exc))
            log_line = {
                "ts": ts,
                "level": "ERROR",
                "iteration": iteration,
                "status": "error",
                "error": str(exc),
            }

        # Emit structured JSON log line to stdout.
        print(json.dumps(log_line), flush=True)

        if max_iterations and iteration >= max_iterations:
            log.info("loop.max_iterations_reached", max=max_iterations)
            break

        if _SHUTDOWN_REQUESTED:
            break

        log.info("loop.sleeping", seconds=sleep_seconds)
        await asyncio.sleep(sleep_seconds)

    log.info("loop.stopped", iterations=iteration)


# ── CLI ───────────────────────────────────────────────────────────────────────

@click.command()
@click.option("--sleep-seconds", default=_DEFAULT_SLEEP, show_default=True, type=int)
@click.option("--dry-run", is_flag=True, default=False)
@click.option("--ticket", default=None, help="Process a single ticket ID.")
@click.option(
    "--entry",
    default="triage_cycle",
    type=click.Choice(["triage_cycle", "review_cycle"]),
    show_default=True,
)
@click.option(
    "--sop-path",
    default=None,
    type=click.Path(exists=True, path_type=Path),
    envvar="SOP_CONFIG_PATH",
)
@click.option(
    "--max-iterations",
    default=None,
    type=int,
    help="Stop after N iterations (useful for testing).",
)
def main(
    sleep_seconds: int,
    dry_run: bool,
    ticket: str | None,
    entry: str,
    sop_path: Path | None,
    max_iterations: int | None,
) -> None:
    """Start the agent shell loop (Ralph Wiggum loop)."""
    asyncio.run(
        loop(
            sleep_seconds=sleep_seconds,
            dry_run=dry_run,
            ticket_id=ticket,
            entry=entry,
            sop_path=sop_path,
            max_iterations=max_iterations,
        )
    )


if __name__ == "__main__":
    main()
