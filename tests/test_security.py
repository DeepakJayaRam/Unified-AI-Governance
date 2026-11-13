from conftest import login
from test_api_workflows import post, API


def test_authentication_expiry_and_revocation(client):
    assert client.get(API + "/systems").status_code == 401
    assert client.post(API + "/auth/login", json={"email": "admin1@test.invalid", "password": "bad"}).status_code == 401
    headers = login(client)
    assert client.get(API + "/auth/me", headers=headers).status_code == 200
    assert client.post(API + "/auth/logout", headers=headers).status_code == 204
    assert client.get(API + "/auth/me", headers=headers).status_code == 401


def test_tenant_isolation_for_records_evidence_reports_and_references(client, headers):
    other = login(client, "admin2@test.invalid", "tenant-2")
    system = post(client, headers, "/systems", {"name": "Confidential system"})
    evidence = post(client, headers, "/evidence", {"title": "Confidential evidence", "content": "tenant-one-secret", "system_id": system["id"]})
    for path in (f"/systems/{system['id']}", f"/evidence/{evidence['id']}/download", f"/evidence/{evidence['id']}/verify"):
        assert client.get(API + path, headers=other).status_code == 404
    assert client.get(API + "/systems", headers=other).json() == []
    assert "tenant-one-secret" not in client.get(API + "/reports/export", headers=other).text
    assert client.post(API + "/risks", headers=other, json={"system_id": system["id"], "title": "cross tenant"}).status_code == 404
    assert client.patch(API + f"/systems/{system['id']}", headers=other, json={"name": "Hijacked"}).status_code == 404
    assert client.get(API + "/systems", headers={**headers, "X-Tenant-ID": "tenant-2"}).status_code == 403


def test_readonly_role_and_privileged_operations(client, headers):
    viewer = login(client, "viewer@test.invalid")
    assert client.get(API + "/systems", headers=viewer).status_code == 200
    for path, body in (("/systems", {"name": "Denied"}), ("/policies", {"name": "Denied"}), ("/evidence", {"title": "Denied", "content": "no"})):
        assert client.post(API + path, headers=viewer, json=body).status_code == 403
    assert client.post(API + "/tenants", headers=viewer, json={"name": "Denied"}).status_code == 403
    assert client.post(API + "/memberships", headers=headers, json={"email": "admin2@test.invalid", "password": "DontResetPassword!", "name": "Bad", "role": "viewer"}).status_code == 409


def test_strict_input_body_limits_and_headers(client, headers):
    assert client.post(API + "/systems", headers=headers, json={"name": "x", "tenant_id": "tenant-2"}).status_code == 422
    response = client.post(API + "/systems", headers=headers, content="x" * 3_000_001)
    assert response.status_code == 413
    response = client.get(API + "/systems", headers=headers)
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["cache-control"] == "no-store"


def test_login_rate_limit(client):
    codes = [client.post(API + "/auth/login", json={"email": "nobody@test.invalid", "password": "wrong"}).status_code for _ in range(11)]
    assert codes[-1] == 429


def test_policy_decision_privacy_and_error_behaviour(client, headers, monkeypatch):
    policy = post(client, headers, "/policies", {"name": "Protect contacts", "config": {"pii_action": "sanitize", "blocked_terms": ["FORBIDDEN"], "error_action": "review"}})
    result = post(client, headers, "/guardrails/evaluate", {"policy_id": policy["id"], "text": "Contact private@example.invalid"})
    assert result["decision"] == "sanitize"
    assert "private@example.invalid" not in result["sanitized_text"]
    events = client.get(API + "/runtime/events", headers=headers)
    assert "private@example.invalid" not in events.text
    assert "sanitized_text" not in events.text
    result = post(client, headers, "/guardrails/evaluate", {"policy_id": policy["id"], "text": "FORBIDDEN"})
    assert result["decision"] == "block" and result["sanitized_text"] is None
    import uag.runtime
    def fail(*args):
        raise RuntimeError("private details")
    monkeypatch.setattr(uag.runtime, "evaluate", fail)
    result = post(client, headers, "/guardrails/evaluate", {"policy_id": policy["id"], "text": "input"})
    assert result["decision"] == "review"
    assert "private details" not in str(result)


def test_cross_tenant_evidence_attachment(client, headers):
    other = login(client, "admin2@test.invalid", "tenant-2")
    evidence = post(client, headers, "/evidence", {"title": "Private", "content": "secret"})
    system = post(client, other, "/systems", {"name": "Other system"})
    assessment = post(client, other, "/assessments", {"name": "Other review", "framework": "nist_ai_rmf", "system_id": system["id"]})
    response = client.put(API + f"/assessments/{assessment['id']}/controls/GOVERN", headers=other, json={"evidence_ids": [evidence["id"]]})
    assert response.status_code == 404


def test_production_configuration_rejects_unsafe_defaults():
    import pytest
    from uag.config import Settings
    with pytest.raises(ValueError, match="Production requires"):
        Settings(secure_environment=True, database_url="sqlite:///test.db", execution_mode="local")
    with pytest.raises(ValueError, match="explicit origins"):
        Settings(cors_origins=("*",))
