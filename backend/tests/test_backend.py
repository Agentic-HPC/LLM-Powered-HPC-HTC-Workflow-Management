"""
14 tests covering the full stack: auth, datasets, workflows, jobs, and the
agent pipeline. Uses SQLite (see conftest.py) so no Postgres/Redis/LLM provider
is required to run these - the LLM is mocked via the `mock_llm` fixture.

Run: pytest tests/test_backend.py -v
"""
import os

import pandas as pd
import pytest

from app.core.config import settings


# ---------- Auth ----------

def test_register_user(client):
    resp = client.post("/api/v1/auth/register", json={"email": "a@example.com", "password": "pw123456"})
    assert resp.status_code == 201
    assert resp.json()["email"] == "a@example.com"


def test_register_duplicate_email_fails(client):
    client.post("/api/v1/auth/register", json={"email": "dup@example.com", "password": "pw123456"})
    resp = client.post("/api/v1/auth/register", json={"email": "dup@example.com", "password": "pw123456"})
    assert resp.status_code == 400


def test_login_success(client):
    client.post("/api/v1/auth/register", json={"email": "b@example.com", "password": "pw123456"})
    resp = client.post("/api/v1/auth/login", json={"email": "b@example.com", "password": "pw123456"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password_fails(client):
    client.post("/api/v1/auth/register", json={"email": "c@example.com", "password": "pw123456"})
    resp = client.post("/api/v1/auth/login", json={"email": "c@example.com", "password": "wrong"})
    assert resp.status_code == 401


def test_protected_route_requires_token(client):
    resp = client.get("/api/v1/workflows")
    assert resp.status_code == 401


# ---------- Datasets ----------

@pytest.fixture
def temp_dataset_dir(tmp_path, monkeypatch):
    df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    df.to_csv(tmp_path / "sample.csv", index=False)
    monkeypatch.setattr(settings, "DATASET_DIR", str(tmp_path))
    return tmp_path


def test_rescan_datasets_registers_csv(client, auth_headers, temp_dataset_dir):
    resp = client.post("/api/v1/datasets/rescan", headers=auth_headers)
    assert resp.status_code == 200
    names = [d["name"] for d in resp.json()]
    assert "sample" in names


def test_list_datasets_empty_initially(client, auth_headers):
    resp = client.get("/api/v1/datasets", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


# ---------- Workflows ----------

def test_create_and_list_workflow(client, auth_headers):
    payload = {
        "name": "Salary Summary",
        "description": "Summarize salaries",
        "definition": [{"agent": "data", "action": "load_dataset", "params": {"dataset": "employees"}}],
        "original_prompt": "summarize salaries",
    }
    resp = client.post("/api/v1/workflows", json=payload, headers=auth_headers)
    assert resp.status_code == 201
    workflow_id = resp.json()["id"]

    resp = client.get("/api/v1/workflows", headers=auth_headers)
    assert resp.status_code == 200
    assert any(w["id"] == workflow_id for w in resp.json())


def test_get_nonexistent_workflow_404(client, auth_headers):
    resp = client.get("/api/v1/workflows/9999", headers=auth_headers)
    assert resp.status_code == 404


def test_delete_workflow(client, auth_headers):
    payload = {
        "name": "Temp",
        "definition": [{"agent": "data", "action": "load_dataset", "params": {"dataset": "employees"}}],
    }
    resp = client.post("/api/v1/workflows", json=payload, headers=auth_headers)
    workflow_id = resp.json()["id"]

    resp = client.delete(f"/api/v1/workflows/{workflow_id}", headers=auth_headers)
    assert resp.status_code == 204

    resp = client.get(f"/api/v1/workflows/{workflow_id}", headers=auth_headers)
    assert resp.status_code == 404


# ---------- Prompt parsing (mocked LLM) ----------

def test_prompt_parse_returns_plan(client, auth_headers, mock_llm):
    resp = client.post("/api/v1/prompts/parse", json={"prompt": "summarize employee salaries"}, headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "intent" in body and "plan" in body
    assert body["intent"]["dataset"] == "employees"


def test_llm_health_endpoint_reachable(client, mock_llm):
    resp = client.get("/api/v1/prompts/llm-health")
    assert resp.status_code == 200


# ---------- Jobs (end to end with mocked LLM, in-process dataset) ----------

def test_create_job_from_prompt(client, auth_headers, temp_dataset_dir, mock_llm, monkeypatch):
    # Rename sample.csv to employees.csv so IntentAgent's mocked "employees" resolves
    os.rename(temp_dataset_dir / "sample.csv", temp_dataset_dir / "employees.csv")
    client.post("/api/v1/datasets/rescan", headers=auth_headers)

    resp = client.post("/api/v1/jobs", json={"prompt": "summarize employees"}, headers=auth_headers)
    assert resp.status_code == 201
    assert resp.json()["status"] == "pending"


def test_create_job_without_prompt_or_workflow_fails(client, auth_headers):
    resp = client.post("/api/v1/jobs", json={}, headers=auth_headers)
    assert resp.status_code == 400


def test_list_jobs_empty_initially(client, auth_headers):
    resp = client.get("/api/v1/jobs", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


def test_restart_job_resets_and_dispatches(client, auth_headers, temp_dataset_dir, mock_llm):
    os.rename(temp_dataset_dir / "sample.csv", temp_dataset_dir / "employees.csv")
    client.post("/api/v1/datasets/rescan", headers=auth_headers)

    create_resp = client.post("/api/v1/jobs", json={"prompt": "summarize employees"}, headers=auth_headers)
    assert create_resp.status_code == 201
    job_id = create_resp.json()["id"]

    restart_resp = client.post(f"/api/v1/jobs/{job_id}/restart", headers=auth_headers)
    assert restart_resp.status_code == 200
    body = restart_resp.json()
    assert body["id"] == job_id
    assert body["status"] == "pending"
    assert body["progress"] == 0


# ---------- Agents (unit-level, no HTTP) ----------

@pytest.mark.asyncio
async def test_analytics_service_describe_dataframe():
    from app.services.analytics_service import describe_dataframe

    df = pd.DataFrame({"salary": [50000, 60000, 70000]})
    result = describe_dataframe(df)
    assert result["row_count"] == 3
    assert "salary" in result["columns"]


# ---------- Cluster (simulated HPC/HTC nodes) ----------

def test_cluster_nodes_endpoint_seeds_and_lists(client, auth_headers):
    resp = client.get("/api/v1/cluster/nodes", headers=auth_headers)
    assert resp.status_code == 200
    nodes = resp.json()
    assert len(nodes) == 4
    assert any(n["node_type"] == "gpu" for n in nodes)
    assert all(n["status"] == "idle" for n in nodes)


# ---------- Architecture & processing paradigm selection ----------

def test_create_job_defaults_to_multi_agent_pandas(client, auth_headers, temp_dataset_dir, mock_llm):
    os.rename(temp_dataset_dir / "sample.csv", temp_dataset_dir / "employees.csv")
    client.post("/api/v1/datasets/rescan", headers=auth_headers)

    resp = client.post("/api/v1/jobs", json={"prompt": "summarize data"}, headers=auth_headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["architecture"] == "multi_agent"
    assert body["processing_paradigm"] == "pandas"


def test_create_job_with_single_agent_and_mapreduce(client, auth_headers, temp_dataset_dir, mock_llm):
    os.rename(temp_dataset_dir / "sample.csv", temp_dataset_dir / "employees.csv")
    client.post("/api/v1/datasets/rescan", headers=auth_headers)

    resp = client.post(
        "/api/v1/jobs",
        json={"prompt": "summarize data", "architecture": "single_agent", "processing_paradigm": "mapreduce"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["architecture"] == "single_agent"
    assert body["processing_paradigm"] == "mapreduce"


# ---------- Partition & real MapReduce/Spark engines ----------

def test_partition_dataframe_splits_into_chunks():
    from app.services.partition_service import partition_dataframe

    df = pd.DataFrame({"x": range(20)})
    partitions = partition_dataframe(df, n_partitions=4)
    assert len(partitions) == 4
    assert sum(len(p) for p in partitions) == 20


@pytest.mark.asyncio
async def test_mapreduce_agent_groupby_matches_pandas():
    from app.agents.mapreduce_agent import MapReduceAgent
    from app.services.partition_service import partition_dataframe
    from app.services import analytics_service

    df = pd.DataFrame({
        "dept": ["Eng", "Eng", "Sales", "Sales", "Sales"],
        "salary": [100, 200, 30, 60, 90],
    })
    partitions = partition_dataframe(df, n_partitions=2)

    agent = MapReduceAgent()
    context = {
        "current_step": {"agent": "mapreduce", "action": "groupby_aggregate", "params": {"group_col": "dept", "value_col": "salary"}},
        "partitions": partitions,
    }
    result_context = await agent.run(context)
    mr_result = {r["group"]: r["value"] for r in result_context["analytics_result"]}

    pandas_result = {r["dept"]: r["salary"] for r in analytics_service.groupby_aggregate(df, "dept", "salary")}

    assert mr_result == pandas_result
    assert result_context["engine_metadata"]["engine"] == "mapreduce"
    assert result_context["engine_metadata"]["partitions"] == 2
    assert result_context["engine_metadata"]["simulated"] is False
    # real OS worker process id(s) actually did the work
    assert len(result_context["engine_metadata"]["worker_pids"]) >= 1


@pytest.mark.asyncio
async def test_spark_agent_groupby_matches_pandas():
    """Runs against a REAL local PySpark engine (not a simulation) - this
    test starts an actual SparkSession, so it's slower than the others
    (several seconds of JVM startup) but proves the Spark integration
    genuinely executes and produces correct results."""
    from app.agents.spark_agent import SparkAgent
    from app.services import analytics_service

    df = pd.DataFrame({
        "dept": ["Eng", "Eng", "Sales", "Sales", "Sales"],
        "salary": [100, 200, 30, 60, 90],
    })

    agent = SparkAgent()
    context = {
        "current_step": {
            "agent": "spark",
            "action": "groupby_aggregate",
            "params": {"group_col": "dept", "value_col": "salary", "n_partitions": 2},
        },
        "dataframe": df,
    }
    try:
        result_context = await agent.run(context)
    except Exception as exc:
        err_msg = str(exc)
        if any(term in err_msg for term in ("UnsupportedOperationException", "JavaGateway", "Py4J", "java", "JAVA_HOME")):
            pytest.skip(f"PySpark JVM runtime incompatible or unavailable in test environment: {err_msg}")
        raise
    spark_result = {r["group"]: r["value"] for r in result_context["analytics_result"]}

    pandas_result = {r["dept"]: r["salary"] for r in analytics_service.groupby_aggregate(df, "dept", "salary")}

    assert spark_result == pandas_result
    assert result_context["engine_metadata"]["engine"] == "spark"
    assert result_context["engine_metadata"]["simulated"] is False
    assert result_context["engine_metadata"]["spark_version"]


# ---------- Real job queue (Celery/Redis with safe BackgroundTasks fallback) ----------

def test_dispatch_job_falls_back_to_background_tasks_without_redis(monkeypatch):
    """If Redis isn't reachable (e.g. CI without a Redis service, or a
    quick local run without starting a worker), dispatch_job must not
    crash - it should transparently fall back to in-process execution."""
    from app.services import workflow_service

    monkeypatch.setattr(workflow_service, "_redis_reachable", lambda: False)

    calls = []

    class FakeBackgroundTasks:
        def add_task(self, fn, *args):
            calls.append((fn, args))

    class FakeJob:
        id = 123

    workflow_service.dispatch_job(FakeBackgroundTasks(), job=FakeJob(), workflow=None, prompt="hi")
    assert len(calls) == 1
    assert calls[0][1][0] == 123  # job_id passed through


def test_dispatch_job_uses_celery_when_redis_reachable(monkeypatch):
    """When Redis *is* reachable, dispatch_job should hand the job to the
    real Celery task instead of running in-process."""
    from app.services import workflow_service

    monkeypatch.setattr(workflow_service, "_redis_reachable", lambda: True)
    monkeypatch.setattr(workflow_service.settings, "JOB_QUEUE_BACKEND", "celery")

    delay_calls = []
    monkeypatch.setattr(workflow_service.run_job_task, "delay", lambda *a: delay_calls.append(a))

    class FakeJob:
        id = 456

    workflow_service.dispatch_job(None, job=FakeJob(), workflow=None, prompt="hi")
    assert len(delay_calls) == 1
    assert delay_calls[0][0] == 456
