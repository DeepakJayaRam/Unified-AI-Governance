import os
import tempfile
import atexit
from pathlib import Path
import pytest

_workspace = tempfile.TemporaryDirectory(prefix="uag-tests-")
os.environ["DATABASE_URL"] = "sqlite:///" + str(Path(_workspace.name) / "test.db").replace("\\", "/")
os.environ["EXECUTION_MODE"] = "local"
from fastapi.testclient import TestClient
from uag.auth import _attempts, hasher
from uag.db import Base, Membership, SessionLocal, Tenant, User, engine
from uag.main import app
atexit.register(engine.dispose)


@pytest.fixture
def client():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    _attempts.clear()
    password_hash = hasher.hash("Testing-password-2026!")
    with SessionLocal() as db:
        for index in (1, 2):
            tenant = Tenant(id=f"tenant-{index}", name=f"Organisation {index}")
            user = User(id=f"user-{index}", email=f"admin{index}@test.invalid", name=f"Admin {index}", password_hash=password_hash, platform_admin=index == 1)
            db.add_all([tenant, user])
            db.flush()
            db.add(Membership(user_id=user.id, tenant_id=tenant.id, role="organisation_admin"))
        viewer = User(id="viewer", email="viewer@test.invalid", name="Viewer", password_hash=password_hash)
        db.add(viewer)
        db.flush()
        db.add(Membership(user_id=viewer.id, tenant_id="tenant-1", role="viewer"))
        db.commit()
    with TestClient(app) as test_client:
        yield test_client


def login(client, email="admin1@test.invalid", tenant="tenant-1"):
    response = client.post("/api/v1/auth/login", json={"email": email, "password": "Testing-password-2026!"})
    assert response.status_code == 200, response.text
    return {"Authorization": "Bearer " + response.json()["access_token"], "X-Tenant-ID": tenant}


@pytest.fixture
def headers(client):
    return login(client)
