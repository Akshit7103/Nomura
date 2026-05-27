"""Parse a ``.eml`` file into a Microsoft Graph ``message`` resource (JSON).

The mock Graph service holds one *record* per email (the parsed result of
``parse_eml``) and renders the public Graph-shaped JSON on demand via
``render_message`` — so it can honour ``$select``, ``$expand=attachments`` and
the ``Prefer: outlook.body-content-type`` header exactly like real Graph.

Field names mirror Graph v1.0 precisely. A connector written against this mock
therefore runs unchanged against production Graph; only the base URL and
credentials differ. See:
https://learn.microsoft.com/en-us/graph/api/resources/message
"""

import base64
import email
import hashlib
import html as _html
import re
from datetime import datetime, timezone
from email.header import decode_header, make_header
from email.utils import getaddresses, parseaddr, parsedate_to_datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Graph always returns these regardless of $select.
_ALWAYS = {"id", "@odata.etag"}


def _decode(value: Optional[str]) -> str:
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except Exception:  # noqa: BLE001
        return value


def _recipient(raw_name: str, address: str) -> Dict[str, Any]:
    return {"emailAddress": {"name": _decode(raw_name) or address, "address": address}}


def _recipient_list(header_value: Optional[str]) -> List[Dict[str, Any]]:
    if not header_value:
        return []
    out = []
    for name, address in getaddresses([header_value]):
        if address:
            out.append(_recipient(name, address))
    return out


def _iso(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _stable_id(seed: str) -> str:
    """Deterministic, URL-safe id derived from a seed (mirrors Graph's opaque ids)."""
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def _html_to_text(html: str) -> str:
    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", "", html)
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</p\s*>", "\n", text)
    text = re.sub(r"(?i)</li\s*>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    return _html.unescape(text).strip()


def _text_to_html(text: str) -> str:
    return f"<html><body><pre>{_html.escape(text)}</pre></body></html>"


def _payload_text(part) -> str:
    raw = part.get_payload(decode=True) or b""
    charset = part.get_content_charset() or "utf-8"
    try:
        return raw.decode(charset, errors="ignore")
    except LookupError:
        return raw.decode("utf-8", errors="ignore")


def parse_eml(source: Union[str, Path, bytes], *, source_name: Optional[str] = None) -> Dict[str, Any]:
    """Parse a ``.eml`` (path or bytes) into an internal Graph-message record.

    The record carries public Graph fields plus the private ``_body_text`` /
    ``_body_html`` / ``_attachments`` used by :func:`render_message`.
    """
    if isinstance(source, (str, Path)):
        raw = Path(source).read_bytes()
        source_name = source_name or Path(source).stem
    else:
        raw = source
        source_name = source_name or "message"

    msg = email.message_from_bytes(raw)

    body_text, body_html = "", ""
    attachments: List[Dict[str, Any]] = []

    for part in msg.walk():
        if part.is_multipart():
            continue
        ctype = part.get_content_type()
        disp = str(part.get("Content-Disposition", "")).lower()
        filename = part.get_filename()

        if "attachment" in disp or (filename and ctype not in ("text/plain", "text/html")):
            data = part.get_payload(decode=True) or b""
            attachments.append({
                "name": _decode(filename) if filename else "attachment",
                "contentType": ctype,
                "data": data,
                "isInline": "inline" in disp,
                "contentId": (part.get("Content-ID") or "").strip("<>") or None,
            })
        elif ctype == "text/plain" and not body_text:
            body_text = _payload_text(part)
        elif ctype == "text/html" and not body_html:
            body_html = _payload_text(part)

    internet_message_id = (msg.get("Message-ID") or f"<{source_name}@local>").strip()
    msg_id = _stable_id(internet_message_id)
    subject = _decode(msg.get("Subject", ""))
    from_name, from_addr = parseaddr(msg.get("From", ""))
    received = _iso(_safe_date(msg.get("Date")))

    record: Dict[str, Any] = {
        "@odata.etag": f'W/"{_stable_id("etag:" + msg_id)[:22]}"',
        "id": msg_id,
        "createdDateTime": received,
        "lastModifiedDateTime": received,
        "changeKey": _stable_id("ck:" + msg_id)[:22],
        "categories": [],
        "receivedDateTime": received,
        "sentDateTime": received,
        "hasAttachments": bool(attachments),
        "internetMessageId": internet_message_id,
        "subject": subject,
        "bodyPreview": (body_text or _html_to_text(body_html))[:255],
        "importance": "normal",
        "parentFolderId": _stable_id("folder:inbox"),
        "conversationId": _stable_id("conv:" + subject),
        "conversationIndex": base64.b64encode(_stable_id("ci:" + msg_id).encode()[:22]).decode(),
        "isRead": False,
        "isDraft": False,
        "webLink": (
            "https://outlook.office365.com/owa/?ItemID="
            f"{msg_id}&exvsurl=1&viewmodel=ReadMessageItem"
        ),
        "inferenceClassification": "focused",
        "sender": _recipient(from_name, from_addr),
        "from": _recipient(from_name, from_addr),
        "toRecipients": _recipient_list(msg.get("To")),
        "ccRecipients": _recipient_list(msg.get("Cc")),
        "bccRecipients": _recipient_list(msg.get("Bcc")),
        "replyTo": _recipient_list(msg.get("Reply-To")),
        "flag": {"flagStatus": "notFlagged"},
        # -- private (stripped by render_message) --
        "_body_text": body_text,
        "_body_html": body_html,
        "_attachments": [
            {
                "@odata.type": "#microsoft.graph.fileAttachment",
                "id": _stable_id(f"{msg_id}:att:{i}:{a['name']}"),
                "lastModifiedDateTime": received,
                "name": a["name"],
                "contentType": a["contentType"],
                "size": len(a["data"]),
                "isInline": a["isInline"],
                "contentId": a["contentId"],
                "contentBytes": base64.b64encode(a["data"]).decode("ascii"),
            }
            for i, a in enumerate(attachments)
        ],
    }
    return record


def _safe_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None


def render_message(
    record: Dict[str, Any],
    *,
    body_type: str = "html",
    select: Optional[List[str]] = None,
    expand: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Render the public Graph message JSON from an internal record."""
    if body_type == "text":
        content = record["_body_text"] or _html_to_text(record["_body_html"])
        body = {"contentType": "text", "content": content}
    else:
        content = record["_body_html"] or _text_to_html(record["_body_text"])
        body = {"contentType": "html", "content": content}

    msg = {k: v for k, v in record.items() if not k.startswith("_")}
    msg["body"] = body

    if expand and "attachments" in expand:
        msg["attachments"] = [dict(a) for a in record["_attachments"]]

    if select:
        keep = set(select) | _ALWAYS | ({"body"} if "body" in select else set())
        msg = {k: v for k, v in msg.items() if k in keep}
    return msg


def render_attachment(att: Dict[str, Any]) -> Dict[str, Any]:
    return dict(att)
