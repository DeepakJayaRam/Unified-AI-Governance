from conftest import login

API = "/api/v1"


def post(client, headers, path, body):
    response = client.post(API + path, json=body, headers=headers)
    assert response.status_code in {200, 201, 202}, response.text
    return response.json()


def test_complete_governance_workflow(client, headers):
    system = post(client, headers, "/systems", {"name": "Document assistant", "description": "Internal retrieval application"})
    assessment = post(client, headers, "/assessments", {"system_id": system["id"], "framework": "nist_ai_rmf", "name": "Initial review"})
    risk = post(client, headers, "/risks", {"system_id": system["id"], "title": "Unsupported factual output", "severity": "high"})
    finding = post(client, headers, "/findings", {"system_id": system["id"], "title": "Evaluation evidence missing"})
    action = post(client, headers, "/actions", {"system_id": system["id"], "finding_id": finding["id"], "title": "Run factuality evaluation", "owner": "Test owner", "due_date": "2026-12-01"})
    evidence = post(client, headers, "/evidence", {"system_id": system["id"], "title": "Evaluation notes", "content": "Human-reviewed test evidence"})
    update = client.put(API + f"/assessments/{assessment['id']}/controls/MEASURE", headers=headers, json={"status": "implemented", "notes": "Reviewed", "evidence_ids": [evidence["id"]]})
    assert update.status_code == 200, update.text
    assert next(c for c in update.json()["controls"] if c["id"] == "MEASURE")["evidence_ids"] == [evidence["id"]]
    assert client.patch(API + f"/actions/{action['id']}", headers=headers, json={"status": "resolved"}).json()["status"] == "resolved"
    report = client.get(API + "/reports/export", headers=headers)
    assert report.status_code == 200
    assert report.json()["resources"]["risks"][0]["id"] == risk["id"]
    assert "content" not in report.json()["resources"]["evidence"][0]
    metrics = client.get(API + "/dashboard", headers=headers).json()
    assert metrics["systems"] == metrics["evidence"] == metrics["assessments"] == 1
    events = client.get(API + "/audit", headers=headers).json()
    assert len(events) >= 9
    assert events[0]["previous_hash"] == events[1]["event_hash"]


def test_empty_dashboard_and_frameworks(client, headers):
    metrics = client.get(API + "/dashboard", headers=headers).json()
    assert metrics["systems"] == metrics["risks"] == metrics["executions"] == 0
    frameworks = client.get(API + "/frameworks", headers=headers).json()
    assert {f["id"] for f in frameworks} == {"eu_ai_act", "iso42001", "nist_ai_rmf"}


def test_bom_import_comparison(client, headers):
    system = post(client, headers, "/systems", {"name": "Inventory"})
    base = {"bomFormat": "CycloneDX", "specVersion": "1.6", "version": 1}
    first = post(client, headers, "/bom", {"system_id": system["id"], "document": {**base, "components": [{"type": "library", "name": "a"}]}})
    second = post(client, headers, "/bom", {"system_id": system["id"], "document": {**base, "components": [{"type": "library", "name": "b"}]}})
    assert second["comparison"] == {"added": ["b"], "removed": ["a"]}
    assert first["validation"] == "structural_only"


def test_openapi_contract(client):
    schema = client.get(API + "/openapi.json").json()
    assert schema["info"]["version"] == "0.1.0"
    assert "/api/v1/systems" in schema["paths"]
    assert "SystemCreate" in schema["components"]["schemas"]
