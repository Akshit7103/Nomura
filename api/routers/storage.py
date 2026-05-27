"""Storage module exposed as an endpoint — read access to stored cases."""

import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from api.deps import get_config, get_correlation_id, open_db
from api.models import Envelope, success
from config.settings import EmailAgentConfig
from utils.logger import get_logger

router = APIRouter(prefix="/storage", tags=["storage"])
logger = get_logger("api.storage")


@router.get("/cases", response_model=Envelope)
def list_cases(cfg: EmailAgentConfig = Depends(get_config),
               cid: str = Depends(get_correlation_id)) -> Envelope:
    db = open_db(cfg)
    try:
        cases = db.list_cases()
        statuses = db.count_by_status()
    finally:
        db.close()
    return success({"count": len(cases), "by_status": statuses, "cases": cases}, cid)


@router.get("/cases/{trade_id}", response_model=Envelope)
def get_case(trade_id: str,
             cfg: EmailAgentConfig = Depends(get_config),
             cid: str = Depends(get_correlation_id)) -> Envelope:
    db = open_db(cfg)
    try:
        case = db.get_case(trade_id)
    finally:
        db.close()
    if case is None:
        raise HTTPException(404, {"code": "CaseNotFound",
                                  "message": f"No stored case for trade_id '{trade_id}'."})

    manifest = None
    folder = case.get("case_folder")
    if folder:
        mpath = Path(folder) / "manifest.json"
        if mpath.exists():
            manifest = json.loads(mpath.read_text(encoding="utf-8"))
    return success({"case": case, "manifest": manifest}, cid)


@router.get("/stats", response_model=Envelope)
def stats(cfg: EmailAgentConfig = Depends(get_config),
          cid: str = Depends(get_correlation_id)) -> Envelope:
    db = open_db(cfg)
    try:
        cases = db.list_cases()
        by_status = db.count_by_status()
    finally:
        db.close()
    return success({"total_cases": len(cases), "by_status": by_status}, cid)
