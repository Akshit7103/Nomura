"""Classifier module exposed as an endpoint."""

from fastapi import APIRouter, Depends

from api.deps import get_classifier, get_correlation_id
from api.models import ClassifyRequest, Envelope, success
from classifier.rule_classifier import RuleClassifier
from utils.audit import record_audit
from utils.logger import get_logger

router = APIRouter(prefix="/classifier", tags=["classifier"])
logger = get_logger("api.classifier")


@router.post("/classify", response_model=Envelope)
def classify(req: ClassifyRequest,
             classifier: RuleClassifier = Depends(get_classifier),
             cid: str = Depends(get_correlation_id)) -> Envelope:
    result = classifier.classify(req.subject, req.body)
    logger.info("classify -> %s (%.2f) cid=%s", result.label, result.confidence, cid)
    record_audit("email.classified", "success", actor="api-client",
                 resource=result.trade_id or req.subject[:60], correlation_id=cid,
                 label=result.label, confidence=result.confidence)
    return success(result.__dict__, cid)
