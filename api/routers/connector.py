"""Connector module exposed as an endpoint.

Fetches (does not classify or store) from the chosen source and returns a
lightweight summary per email. Proves the source plumbing — local folder or the
Graph API — independently of the rest of the pipeline.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from api.deps import build_connector, get_config, get_correlation_id
from api.models import Envelope, FetchRequest, PreviewRequest, success
from config.settings import EmailAgentConfig
from utils.audit import record_audit
from utils.logger import get_logger

router = APIRouter(prefix="/connector", tags=["connector"])
logger = get_logger("api.connector")


@router.post("/fetch", response_model=Envelope)
def fetch(req: FetchRequest, request: Request,
          cfg: EmailAgentConfig = Depends(get_config),
          cid: str = Depends(get_correlation_id)) -> Envelope:
    connector = build_connector(req.source, cfg, request.app)
    try:
        emails = connector.fetch_emails()
    finally:
        if hasattr(connector, "close"):
            connector.close()

    summaries = [{
        "message_id": e["message_id"],
        "subject": e["subject"],
        "sender": e["sender"],
        "received_at": e["received_at"],
        "has_body": bool(e.get("body")),
        "attachment_count": len(e.get("attachments", [])),
    } for e in emails]

    logger.info("connector.fetch source=%s -> %d emails cid=%s", req.source, len(emails), cid)
    record_audit("graph.fetch" if req.source == "graph" else "connector.fetch",
                 "success", actor="api-client", resource=req.source,
                 correlation_id=cid, count=len(emails))
    return success({"source": req.source, "count": len(emails), "emails": summaries}, cid)


@router.post("/preview", response_model=Envelope)
def preview(req: PreviewRequest, request: Request,
            cfg: EmailAgentConfig = Depends(get_config),
            cid: str = Depends(get_correlation_id)) -> Envelope:
    """Fetch a single email with full body by message_id."""
    connector = build_connector(req.source, cfg, request.app)
    try:
        emails = connector.fetch_emails()
    finally:
        if hasattr(connector, "close"):
            connector.close()

    email = next((e for e in emails if e["message_id"] == req.message_id), None)
    if not email:
        raise HTTPException(status_code=404, detail={
            "code": "EmailNotFound",
            "message": f"No email found with message_id '{req.message_id}'."
        })

    return success({
        "message_id":       email["message_id"],
        "subject":          email["subject"],
        "sender":           email["sender"],
        "received_at":      email["received_at"],
        "body":             email.get("body", ""),
        "attachment_count": len(email.get("attachments", [])),
        "attachments": [
            {"filename": a["filename"], "mime_type": a.get("mime_type", "")}
            for a in email.get("attachments", [])
        ],
    }, cid)
