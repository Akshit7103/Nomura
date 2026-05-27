"""Audit logging — append-only, structured, compliance-grade.

Deliberately separate from ``utils.logger`` (developer logs):

* **Developer logs** (``utils.logger``) are human-readable and level-gated
  (DEBUG/INFO/WARNING). They exist to debug the *logical* flow — what the
  classifier scored, why an email was skipped. They are verbose, can be muted,
  and change freely as the code evolves. A developer reads them, tweaks logic,
  re-runs.

* **Audit logs** (this module) are one JSON object per *business* event, never
  level-gated, written append-only to ``<audit_log_dir>/audit_<date>.log``.
  They answer the question a bank's risk/compliance function asks: *who* did
  *what*, to *which* resource, *when*, and did it *succeed*. Treat the field set
  as a contract — add fields, never repurpose them. In production these are
  shipped to a WORM store / SIEM (Splunk, Microsoft Sentinel) rather than a
  local file, and the local file is the dev-time stand-in.

Every event carries a ``correlation_id`` so a single API request (or agent run)
can be traced across the developer log, the audit log, and the response header.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

_AUDIT_LOGGER_NAME = "audit"
_current_dir: str | None = None


def setup_audit(log_dir: str = "logs") -> None:
    """Attach a dedicated file handler for the audit stream (idempotent per dir)."""
    global _current_dir
    if _current_dir == log_dir:
        return

    Path(log_dir).mkdir(parents=True, exist_ok=True)
    path = Path(log_dir) / f"audit_{datetime.now(timezone.utc):%Y%m%d}.log"

    handler = logging.FileHandler(path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(message)s"))  # message is already JSON

    lg = logging.getLogger(_AUDIT_LOGGER_NAME)
    lg.setLevel(logging.INFO)
    lg.propagate = False  # keep the audit trail out of the developer console/file
    # Replace any prior file handler so a changed log_dir (e.g. tests) takes effect.
    for h in [h for h in lg.handlers if isinstance(h, logging.FileHandler)]:
        lg.removeHandler(h)
        h.close()
    lg.addHandler(handler)
    _current_dir = log_dir


def record_audit(
    action: str,
    outcome: str,
    *,
    actor: str = "system",
    resource: str | None = None,
    correlation_id: str | None = None,
    log_dir: str = "logs",
    **details,
) -> dict:
    """Append one audit event and return it.

    Args:
        action:   dotted business action, e.g. ``email.classified``, ``agent.run``,
                  ``graph.fetch``, ``api.request``, ``case.stored``.
        outcome:  ``success`` | ``failure`` | ``skipped``.
        actor:    who triggered it (``system``, ``api-client``, a user id, ...).
        resource: the thing acted on (trade id, message id, endpoint path).
        details:  any extra structured context (kept under ``details``).
    """
    setup_audit(log_dir)
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_id": str(uuid.uuid4()),
        "correlation_id": correlation_id,
        "actor": actor,
        "action": action,
        "resource": resource,
        "outcome": outcome,
        "details": details,
    }
    logging.getLogger(_AUDIT_LOGGER_NAME).info(json.dumps(event, default=str))
    return event


def new_correlation_id() -> str:
    return str(uuid.uuid4())
