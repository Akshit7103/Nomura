"""Agent runner exposed as an endpoint — runs the full Sense→Plan→Act→Reflect pipeline."""

from fastapi import APIRouter, Depends, Request

from agent.email_agent import EmailAgentRunner
from api.deps import build_connector, get_classifier, get_config, get_correlation_id, open_db, open_store
from api.models import Envelope, RunRequest, success
from config.settings import EmailAgentConfig
from utils.logger import get_logger

router = APIRouter(prefix="/agent", tags=["agent"])
logger = get_logger("api.agent")


@router.post("/run", response_model=Envelope)
def run(req: RunRequest, request: Request,
        cfg: EmailAgentConfig = Depends(get_config),
        cid: str = Depends(get_correlation_id)) -> Envelope:
    connector = build_connector(req.source, cfg, request.app)
    classifier = get_classifier(cfg)
    store = open_store(cfg)
    db = open_db(cfg)
    try:
        runner = EmailAgentRunner(cfg, connector, classifier, store, db)
        stats = runner.run(correlation_id=cid)
    finally:
        db.close()
        if hasattr(connector, "close"):
            connector.close()

    logger.info("agent.run source=%s -> relevant=%d ambiguous=%d irrelevant=%d duplicate=%d cid=%s",
                req.source, stats.relevant, stats.ambiguous, stats.irrelevant, stats.duplicate, cid)

    stats_dict = {k: v for k, v in stats.__dict__.items() if k != "classified_emails"}
    return success({
        "source": req.source,
        "stats": stats_dict,
        "classified_emails": stats.classified_emails,
    }, cid)
