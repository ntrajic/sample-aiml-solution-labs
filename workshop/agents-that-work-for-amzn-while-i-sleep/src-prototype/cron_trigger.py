"""
triggers/cron_trigger.py
Cron trigger — one-shot invocation of the SOP Engine, designed to be scheduled
via cron, systemd timers, or a task scheduler.

Recommended crontab entry:
    # Triage cycle every 15 minutes
    */15 * * * *  cd /path/to/project && python -m triggers.cron_trigger

    # Review cycle every 10 minutes
    */10 * * * *  cd /path/to/project && python -m triggers.cron_trigger --entry review_cycle

Exit codes:
    0 — Success (including "no work found").
    1 — Unexpected error.
    2 — Configuration error (bad SOP path, missing env vars).
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import click
import structlog

logger = structlog.get_logger(__name__)


async def _one_shot(
    *,
    entry: str,
    dry_run: bool,
    ticket_id: str | None,
    sop_path: Path | None,
) -> int:
    """
    Run one SOP cycle and return an exit code.

    Returns 0 on success, 1 on error.
    """
    from orchestration.sop_engine import SOPEngine

    ts = datetime.now(timezone.utc).isoformat()
    log = logger.bind(entry=entry, dry_run=dry_run, ts=ts)
    log.info("cron.start")

    try:
        engine = SOPEngine(sop_path=sop_path, dry_run=dry_run)
        engine.load()

        if entry == "triage_cycle":
            results = await engine.run_triage_cycle(ticket_id=ticket_id)
        elif entry == "review_cycle":
            results = await engine.run_review_cycle()
        else:
            raise ValueError(f"Unknown entry point: {entry!r}")

        summary = {
            "ts": ts,
            "level": "INFO",
            "status": "success",
            "entry": entry,
            "processed": len(results),
            "tickets": [r.payload.get("ticket_id", "") for r in results],
        }
        print(json.dumps(summary), flush=True)
        log.info("cron.done", processed=len(results))
        return 0

    except (KeyError, FileNotFoundError, ValueError) as exc:
        error_summary = {
            "ts": ts,
            "level": "ERROR",
            "status": "config_error",
            "entry": entry,
            "error": str(exc),
        }
        print(json.dumps(error_summary), flush=True)
        log.error("cron.config_error", error=str(exc))
        return 2

    except Exception as exc:  # noqa: BLE001
        error_summary = {
            "ts": ts,
            "level": "ERROR",
            "status": "error",
            "entry": entry,
            "error": str(exc),
        }
        print(json.dumps(error_summary), flush=True)
        log.exception("cron.error", error=str(exc))
        return 1


# ── Cron schedule validation helper ──────────────────────────────────────────

def validate_cron_expression(expression: str) -> bool:
    """
    Basic validation of a cron expression using croniter.
    Returns True if valid, False otherwise.
    """
    try:
        from croniter import croniter
        return croniter.is_valid(expression)
    except ImportError:
        logger.warning("cron.validate.croniter_unavailable")
        return True  # Assume valid if croniter not installed.


def next_run_times(expression: str, count: int = 5) -> list[datetime]:
    """Return the next *count* scheduled run times for a cron expression."""
    from croniter import croniter
    base = datetime.now(timezone.utc)
    cron = croniter(expression, base)
    return [cron.get_next(datetime) for _ in range(count)]


# ── CLI ───────────────────────────────────────────────────────────────────────

@click.command()
@click.option(
    "--entry",
    default="triage_cycle",
    type=click.Choice(["triage_cycle", "review_cycle"]),
    show_default=True,
)
@click.option("--dry-run", is_flag=True, default=False, envvar="AGENT_DRY_RUN")
@click.option("--ticket", default=None, help="Process a single ticket ID (triage only).")
@click.option(
    "--sop-path",
    default=None,
    type=click.Path(path_type=Path),
    envvar="SOP_CONFIG_PATH",
)
@click.option(
    "--validate-cron",
    default=None,
    help="Validate a cron expression and print next 5 run times, then exit.",
)
def main(
    entry: str,
    dry_run: bool,
    ticket: str | None,
    sop_path: Path | None,
    validate_cron: str | None,
) -> None:
    """One-shot cron-compatible agent trigger."""

    if validate_cron:
        valid = validate_cron_expression(validate_cron)
        if valid:
            times = next_run_times(validate_cron)
            click.echo(f"Expression {validate_cron!r} is valid.")
            click.echo("Next 5 runs:")
            for t in times:
                click.echo(f"  {t.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        else:
            click.echo(f"Expression {validate_cron!r} is INVALID.", err=True)
            sys.exit(2)
        return

    exit_code = asyncio.run(
        _one_shot(
            entry=entry,
            dry_run=dry_run,
            ticket_id=ticket,
            sop_path=sop_path,
        )
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
