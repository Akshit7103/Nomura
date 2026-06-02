"""Tests that the mock Graph service replicates the real Graph v1.0 response shape."""

MAILBOX = "mo-team@nomura.com"
TOKEN_PATH = "/mock-tenant-id/oauth2/v2.0/token"
AUTH = {"Authorization": "Bearer test-token"}


def _get_token(client) -> str:
    resp = client.post(TOKEN_PATH, data={
        "grant_type": "client_credentials",
        "client_id": "mock-client-id",
        "client_secret": "mock-client-secret",
    })
    assert resp.status_code == 200
    return resp.json()["access_token"]


def test_token_endpoint(mock_client):
    body = mock_client.post(TOKEN_PATH, data={
        "grant_type": "client_credentials",
        "client_id": "mock-client-id",
        "client_secret": "mock-client-secret",
    }).json()
    assert body["token_type"] == "Bearer"
    assert body["access_token"]
    assert body["expires_in"] == 3599


def test_token_rejects_wrong_grant(mock_client):
    resp = mock_client.post(TOKEN_PATH, data={
        "grant_type": "password",
        "client_id": "x", "client_secret": "y",
    })
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "unsupported_grant_type"


def test_messages_require_bearer(mock_client):
    resp = mock_client.get(f"/v1.0/users/{MAILBOX}/messages")
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "InvalidAuthenticationToken"


def test_list_envelope_and_paging(mock_client):
    resp = mock_client.get(f"/v1.0/users/{MAILBOX}/messages?$top=10&$count=true", headers=AUTH)
    assert resp.status_code == 200
    data = resp.json()
    assert "@odata.context" in data
    assert isinstance(data["value"], list)
    assert len(data["value"]) == 10
    assert data["@odata.count"] == 27
    assert "@odata.nextLink" in data  # 27 > 10 -> more pages

    # walk all pages -> exactly 27
    total = len(data["value"])
    next_link = data["@odata.nextLink"]
    while next_link:
        page = mock_client.get(next_link, headers=AUTH).json()
        total += len(page["value"])
        next_link = page.get("@odata.nextLink")
    assert total == 27


def test_message_fields_match_graph_schema(mock_client):
    first = mock_client.get(f"/v1.0/users/{MAILBOX}/messages?$top=1", headers=AUTH).json()["value"][0]
    for key in ("id", "internetMessageId", "subject", "from", "sender",
                "toRecipients", "receivedDateTime", "hasAttachments", "body", "webLink"):
        assert key in first, f"missing Graph field: {key}"
    assert first["from"]["emailAddress"]["address"]


def test_prefer_text_body(mock_client):
    headers = {**AUTH, "Prefer": 'outlook.body-content-type="text"'}
    msg = mock_client.get(f"/v1.0/users/{MAILBOX}/messages?$top=1", headers=headers).json()["value"][0]
    assert msg["body"]["contentType"] == "text"


def test_get_single_message_and_404(mock_client):
    listed = mock_client.get(f"/v1.0/users/{MAILBOX}/messages?$top=1", headers=AUTH).json()["value"][0]
    mid = listed["id"]
    one = mock_client.get(f"/v1.0/users/{MAILBOX}/messages/{mid}", headers=AUTH)
    assert one.status_code == 200
    assert one.json()["id"] == mid

    missing = mock_client.get(f"/v1.0/users/{MAILBOX}/messages/does-not-exist", headers=AUTH)
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "ErrorItemNotFound"


def test_attachments_endpoint_present(mock_client):
    # synthetic emails carry no file attachments -> endpoint returns an empty collection
    mid = mock_client.get(f"/v1.0/users/{MAILBOX}/messages?$top=1", headers=AUTH).json()["value"][0]["id"]
    resp = mock_client.get(f"/v1.0/users/{MAILBOX}/messages/{mid}/attachments", headers=AUTH)
    assert resp.status_code == 200
    assert "value" in resp.json()
