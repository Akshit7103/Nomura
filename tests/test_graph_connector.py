"""Tests the GraphConnector against the live mock Graph server (real HTTP)."""


def test_fetch_returns_normalized_dicts(graph_connector):
    emails = graph_connector.fetch_emails()
    assert len(emails) == 27

    sample = emails[0]
    # exactly the shape LocalEmailConnector produces
    for key in ("message_id", "subject", "sender", "received_at",
                "body", "html_body", "attachments", "source_file"):
        assert key in sample
    assert isinstance(sample["attachments"], list)


def test_message_id_is_internet_message_id(graph_connector):
    emails = graph_connector.fetch_emails()
    # generator uses <...@synthetic.local> internet message ids
    assert all(e["message_id"].startswith("<") for e in emails)
    assert any("@synthetic.local" in e["message_id"] for e in emails)


def test_fx_trade_body_is_present_and_text(graph_connector):
    emails = graph_connector.fetch_emails()
    trade = next(e for e in emails if "FX Trade Settlement" in e["subject"])
    assert "FXOPT-2026-" in trade["subject"]
    assert "Settlement" in trade["body"] or "settlement" in trade["body"]


def test_paging_is_followed(graph_connector):
    # page_size=10 over 27 emails means the connector must follow nextLink twice
    emails = graph_connector.fetch_emails()
    assert len(emails) == 27  # nothing dropped or duplicated across pages
    assert len({e["message_id"] for e in emails}) == 27
