import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["SECRET_KEY"] = "test-secret"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.main import app

TEST_DB_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function", autouse=True)
def _fresh_db():
    import app.models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    client.post("/api/v1/auth/register", json={"email": "test@example.com", "password": "secret123"})
    resp = client.post("/api/v1/auth/login", json={"email": "test@example.com", "password": "secret123"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_llm(monkeypatch):
    """Replace llm_service calls so tests don't need a real LLM provider."""
    from app.services import llm_service as llm_module

    async def fake_generate_json(prompt, system=None):
        return {
            "goal": "Summarize the dataset",
            "dataset": "employees",
            "analysis_type": "summary",
            "target_columns": ["salary"],
            "group_by": None,
            "output_format": "narrative",
        }

    async def fake_generate(prompt, system=None):
        return "This is a mocked narrative report generated without calling a real LLM."

    monkeypatch.setattr(llm_module.llm_service, "generate_json", fake_generate_json)
    monkeypatch.setattr(llm_module.llm_service, "generate", fake_generate)
    return llm_module.llm_service
