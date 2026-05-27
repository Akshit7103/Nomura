"""Reads emails from Microsoft Graph (or the mock Graph service) over HTTP.

Emits the *same* normalized email dict as ``LocalEmailConnector`` so the rest of
the pipeline (classifier, store, dedup) is unchanged. Swapping from the mock to
production Graph is a base-URL + credentials change — no code change here.

Flow per ``fetch_emails()``:
    1. OAuth2 client-credentials → access token
    2. GET the inbox messages, following ``@odata.nextLink`` paging
    3. For messages with attachments, GET the attachments and base64-decode
    4. Map Graph fields → the normalized dict the agent consumes
"""

import base64
from typing import Any, Dict, List, Optional

import httpx

from utils.logger import get_logger

logger = get_logger("graph_connector")


class GraphConnector:
    def __init__(
        self,
        *,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        mailbox: str,
        base_url: Optional[str] = None,
        folder: str = "inbox",
        page_size: int = 10,
        prefer_text: bool = True,
        client: Optional[httpx.Client] = None,
        timeout: float = 30.0,
    ):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.mailbox = mailbox
        self.folder = folder
        self.page_size = page_size
        self.prefer_text = prefer_text
        # Injected client (tests use httpx ASGITransport); otherwise own one.
        self._owns_client = client is None
        self.client = client or httpx.Client(base_url=base_url or "", timeout=timeout)

    def close(self) -> None:
        if self._owns_client:
            self.client.close()

    # -- OAuth2 -------------------------------------------------------------
    def _get_token(self) -> str:
        resp = self.client.post(
            f"/{self.tenant_id}/oauth2/v2.0/token",
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "scope": "https://graph.microsoft.com/.default",
            },
        )
        resp.raise_for_status()
        return resp.json()["access_token"]

    # -- Fetch --------------------------------------------------------------
    def fetch_emails(self) -> List[Dict[str, Any]]:
        token = self._get_token()
        headers = {"Authorization": f"Bearer {token}"}
        if self.prefer_text:
            headers["Prefer"] = 'outlook.body-content-type="text"'

        url: Optional[str] = (
            f"/v1.0/users/{self.mailbox}/mailFolders/{self.folder}/messages"
            f"?$top={self.page_size}"
        )
        emails: List[Dict[str, Any]] = []
        pages = 0
        while url:
            resp = self.client.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            for gmsg in data.get("value", []):
                emails.append(self._normalize(gmsg, headers))
            url = data.get("@odata.nextLink")
            pages += 1

        logger.info("GraphConnector fetched %d messages across %d page(s) from %s",
                    len(emails), pages, self.mailbox)
        return emails

    def _fetch_attachments(self, message_id: str, headers: Dict[str, str]) -> List[Dict[str, Any]]:
        resp = self.client.get(
            f"/v1.0/users/{self.mailbox}/messages/{message_id}/attachments",
            headers=headers,
        )
        resp.raise_for_status()
        out = []
        for att in resp.json().get("value", []):
            if not att.get("@odata.type", "").endswith("fileAttachment"):
                continue  # skip item/reference attachments — not files
            try:
                data = base64.b64decode(att.get("contentBytes", "") or "")
            except Exception:  # noqa: BLE001
                data = b""
            out.append({
                "filename": att.get("name", "attachment"),
                "data": data,
                "mime_type": att.get("contentType", ""),
            })
        return out

    def _normalize(self, gmsg: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        attachments: List[Dict[str, Any]] = []
        if gmsg.get("hasAttachments"):
            attachments = self._fetch_attachments(gmsg["id"], headers)

        ea = (gmsg.get("from") or {}).get("emailAddress", {})
        name, address = ea.get("name", ""), ea.get("address", "")
        sender = f"{name} <{address}>".strip() if address else name

        body_obj = gmsg.get("body") or {}
        return {
            "message_id": (gmsg.get("internetMessageId") or gmsg.get("id") or "").strip(),
            "subject": gmsg.get("subject", "") or "",
            "sender": sender,
            "received_at": gmsg.get("receivedDateTime", "") or "",
            "body": body_obj.get("content", "") if body_obj.get("contentType") == "text" else body_obj.get("content", ""),
            "html_body": body_obj.get("content", "") if body_obj.get("contentType") == "html" else "",
            "attachments": attachments,
            "source_file": gmsg.get("webLink") or f"graph:{gmsg.get('id', '')}",
        }
