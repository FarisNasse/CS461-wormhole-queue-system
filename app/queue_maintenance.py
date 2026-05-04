"""Queue maintenance helpers and CLI commands."""

from __future__ import annotations

from datetime import datetime, timezone

import click
from flask import Flask

from app import db
from app.models import Ticket


def flush_open_tickets(reason: str = "Queue Flushed") -> int:
    """Close all active tickets and return how many were updated."""
    now = datetime.now(timezone.utc)
    count = Ticket.query.filter(~Ticket.status.in_(["closed", "resolved"])).update(
        {
            Ticket.status: "closed",
            Ticket.closed_reason: reason,
            Ticket.closed_at: now,
            Ticket.number_of_students: 0,
        },
        synchronize_session=False,
    )

    db.session.commit()
    return count


def register_queue_maintenance_cli(app: Flask) -> None:
    """Register queue maintenance commands on the Flask app."""

    @app.cli.command("flush-open-tickets")
    @click.option(
        "--reason",
        default="Queue Flushed",
        show_default=True,
        help="Reason stored in closed_reason for auto-closed tickets.",
    )
    def flush_open_tickets_command(reason: str) -> None:
        """Close all non-closed/resolved tickets."""
        count = flush_open_tickets(reason=reason)
        click.echo(f"Nightly queue flush complete: {count} ticket(s) closed")
