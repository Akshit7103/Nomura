"""Unit tests for the .eml -> Graph message converter."""

import base64
from email.message import EmailMessage

from mock_graph.eml_to_graph import parse_eml, render_message


def _build_eml_with_attachment() -> bytes:
    msg = EmailMessage()
    msg["From"] = "Aastha Makkar (IND) <aastha.makkar@protivitiglobal.in>"
    msg["To"] = "Akshit Mahajan <akshit.mahajan@protivitiglobal.in>"
    msg["Subject"] = "FX Trade Settlement[FXOPT-2026-00047] - USD/JPY"
    msg["Message-ID"] = "<FXOPT-2026-00047-test@synthetic.local>"
    msg["Date"] = "Tue, 26 May 2026 09:14:22 +0000"
    msg.set_content("Deal Reference: FXOPT-2026-00047\nCurrency Pair: USD/JPY\n")
    msg.add_alternative("<html><body><p>Deal Reference: FXOPT-2026-00047</p></body></html>",
                        subtype="html")
    msg.add_attachment(b"%PDF-1.4 fake pdf bytes", maintype="application",
                       subtype="pdf", filename="confirm_FXOPT-2026-00047.pdf")
    return msg.as_bytes()


def test_parse_maps_core_graph_fields():
    record = parse_eml(_build_eml_with_attachment(), source_name="test")
    assert record["internetMessageId"] == "<FXOPT-2026-00047-test@synthetic.local>"
    assert record["subject"].startswith("FX Trade Settlement[FXOPT-2026-00047]")
    assert record["from"]["emailAddress"]["address"] == "aastha.makkar@protivitiglobal.in"
    assert record["from"]["emailAddress"]["name"] == "Aastha Makkar (IND)"
    assert record["receivedDateTime"] == "2026-05-26T09:14:22Z"
    assert record["hasAttachments"] is True
    assert record["id"]  # stable, non-empty


def test_attachment_contentbytes_roundtrip():
    record = parse_eml(_build_eml_with_attachment())
    atts = record["_attachments"]
    assert len(atts) == 1
    att = atts[0]
    assert att["@odata.type"] == "#microsoft.graph.fileAttachment"
    assert att["name"] == "confirm_FXOPT-2026-00047.pdf"
    assert att["contentType"] == "application/pdf"
    assert base64.b64decode(att["contentBytes"]) == b"%PDF-1.4 fake pdf bytes"
    assert att["size"] == len(b"%PDF-1.4 fake pdf bytes")


def test_render_prefers_text_body():
    record = parse_eml(_build_eml_with_attachment())
    rendered = render_message(record, body_type="text")
    assert rendered["body"]["contentType"] == "text"
    assert "Deal Reference: FXOPT-2026-00047" in rendered["body"]["content"]
    # private fields are stripped from the public Graph message
    assert not any(k.startswith("_") for k in rendered)


def test_render_select_limits_fields():
    record = parse_eml(_build_eml_with_attachment())
    rendered = render_message(record, select=["subject", "receivedDateTime"])
    assert set(rendered) <= {"id", "@odata.etag", "subject", "receivedDateTime", "body"}
    assert "subject" in rendered
    assert "from" not in rendered
