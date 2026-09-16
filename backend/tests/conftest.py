import os
import sys
import tempfile
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

# core.config 가 import 되기 전에 테스트용 환경을 고정한다
_tmp = tempfile.mkdtemp(prefix="stellia-test-")
os.environ.setdefault("JWT_SECRET", "test-secret-key-0123456789abcdef0123456789")
os.environ.setdefault("GEMINI_API_KEY", "test-key")
os.environ["ENV"] = "development"
os.environ["DB_PATH"] = str(Path(_tmp) / "test.db")
os.environ["UPLOAD_DIR"] = str(Path(_tmp) / "images")
os.environ["RUN_SCHEDULER"] = "0"
os.environ["RATE_LIMIT_ENABLED"] = "0"  # 레이트리밋 자체는 별도 테스트에서 검증

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture(scope="session")
def client():
    import main
    with TestClient(main.app) as c:
        yield c


def _register(c, email, password="testpw123", username=None):
    r = c.post("/auth/register", json={
        "email": email, "username": username or email.split("@")[0], "password": password
    })
    assert r.status_code == 200, r.text
    return r.json()


@pytest.fixture(scope="session")
def user_a(client):
    return _register(client, "alice@example.com", username="alice")


@pytest.fixture(scope="session")
def user_b(client):
    return _register(client, "bob@example.com", username="bob")


@pytest.fixture(scope="session")
def user_admin(client):
    """관리자 전용 계정.

    일반 유저를 승격시키면 다른 테스트의 '403 이어야 한다' 검증이 깨지므로
    관리자는 별도 계정으로 분리한다.
    """
    import sqlite3
    from core.config import DB_PATH

    tok = _register(client, "admin@example.com", username="admin")
    uid = client.get("/users/me", headers=auth(tok)).json()["id"]
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE users SET is_admin = 1 WHERE id = ?", (uid,))
    conn.commit()
    conn.close()
    return tok


def auth(tok):
    return {"Authorization": f"Bearer {tok['access_token']}"}
