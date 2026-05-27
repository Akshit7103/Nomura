"""Reads .eml files from a local inbox folder into a unified email dict."""

import email
from email.header import decode_header, make_header
from pathlib import Path
from typing import Any, Dict, List

from utils.logger import get_logger

logger = get_logger(__name__)


class LocalEmailConnector:
    """Parse every .eml file in a folder into normalized email dictionaries."""

    def __init__(self, inbox_path: str):
        self.inbox_path = Path(inbox_path)

    def fetch_emails(self) -> List[Dict[str, Any]]:
        if not self.inbox_path.exists():
            logger.warning("Inbox path does not exist: %s", self.inbox_path)
            return []

        emails: List[Dict[str, Any]] = []
        for path in sorted(self.inbox_path.glob("*.eml")):
            try:
                emails.append(self._parse_eml(path))
            except Exception as exc:  # noqa: BLE001 - never let one bad file stop the batch
                logger.warning("Failed to parse %s: %s", path.name, exc)
        logger.info("Fetched %d emails from %s", len(emails), self.inbox_path)
        return emails

    def _parse_eml(self, path: Path) -> Dict[str, Any]:
        with open(path, "rb") as fh:
            msg = email.message_from_bytes(fh.read())

        body, html_body = "", ""
        attachments: List[Dict[str, Any]] = []

        for part in msg.walk():
            if part.is_multipart():
                continue
            ctype = part.get_content_type()
            disp = str(part.get("Content-Disposition", ""))
            filename = part.get_filename()

            if "attachment" in disp.lower() or filename:
                payload = part.get_payload(decode=True) or b""
                attachments.append({
                    "filename": self._decode(filename) if filename else "attachment",
                    "data": payload,
                    "mime_type": ctype,
                })
            elif ctype == "text/plain" and not body:
                body = self._payload_text(part)
            elif ctype == "text/html" and not html_body:
                html_body = self._payload_text(part)

        return {
            "message_id": (msg.get("Message-ID") or path.stem).strip(),
            "subject": self._decode(msg.get("Subject", "")),
            "sender": self._decode(msg.get("From", "")),
            "received_at": msg.get("Date", ""),
            "body": body,
            "html_body": html_body,
            "attachments": attachments,
            "source_file": str(path),
        }

    @staticmethod
    def _payload_text(part) -> str:
        raw = part.get_payload(decode=True) or b""
        charset = part.get_content_charset() or "utf-8"
        try:
            return raw.decode(charset, errors="ignore")
        except LookupError:
            return raw.decode("utf-8", errors="ignore")

    @staticmethod
    def _decode(value: str) -> str:
        if not value:
            return ""
        try:
            return str(make_header(decode_header(value)))
        except Exception:  # noqa: BLE001
            return value
