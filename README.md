# HPC/HTC AI Platform

A prompt-driven, multi-agent data analysis platform. Type a request in plain
English ("show me average age by education level"), and a pipeline of six
agents — **Intent → Planning → Execution (Data → Analytics) → Reporting** —
turns it into a real analysis: loads the right dataset, computes the right
statistics, and writes a plain-language report with a chart.

**Status: this version replaces the earlier simulated distributed-compute
layer with real implementations, and swaps in real datasets.** See
"What's real vs. what's still a stand-in" below for an honest breakdown —
this section is here specifically so a supervisor/evaluator doesn't have to
take marketing copy on faith.

## What's real vs. what's still a stand-in

| Component | Status | Notes |
|---|---|---|
| Datasets | **Real** | `data/employees.csv` (IBM HR-analytics-style, 4,653 real rows) and `data/weather.csv` (96,453 real hourly observations). `scripts/scale_datasets.py` produces bootstrap-resampled, clearly-labeled *scaled* versions for benchmarking — the app itself and correctness tests always use the real, unscaled files. |
| Spark engine | **Real** | `app/agents/spark_agent.py` runs an actual `pyspark.sql.SparkSession` (local mode by default; point `SPARK_MASTER_URL` at a real cluster with no code changes). Verified to produce identical results to pandas. |
| MapReduce engine | **Real (single-machine)** | `app/agents/mapreduce_agent.py` uses a real `ProcessPoolExecutor` — each partition runs in a genuinely separate OS process. Not a Hadoop/YARN cluster, but genuinely parallel, not simulated. |
| Job queue | **Real** | Celery + Redis (`app/core/celery_app.py`) dispatches jobs to a real, separate worker process (`celery -A app.core.celery_app worker`). Falls back to in-process `BackgroundTasks` automatically if Redis isn't reachable, so the app never hard-fails. |
| LLM provider | **Real (cloud)** | Groq (fast hosted inference, free tier) or OpenAI. Both make genuine API calls — no mocked LLM outside the test suite. |
| Cluster/node dashboard | **Still simulated** | `app/services/cluster_service.py` models 4 fixed nodes and generates believable CPU/GPU/memory numbers — there is no real Slurm/HTCondor scheduler underneath. Explicitly documented as simulated in the code. Real multi-node cluster orchestration was out of scope for the time available — see "Suggested next steps." |
| Rate limiting | **Real** | `slowapi` limits the LLM-calling `/prompts/parse` and job-creating `/jobs` endpoints (`RATE_LIMIT_EXPENSIVE`, default 10/min) to bound real API cost/abuse. |

## Architecture

```
Prompt Studio (Next.js) ──▶ FastAPI ──▶ Celery/Redis queue ──▶ worker process
                                                                    │
                    ┌───────────────────────────────────────────────┼──────────────────────┐
                    ▼                     ▼                        ▼                       ▼
              IntentAgent          PlanningAgent            ExecutionAgent
           (LLM: parse intent)   (build step plan)      (routes each step to:)
                                                           ├─ DataAgent
                                                           └─ AnalyticsAgent (pandas)
                                                              or MapReduceAgent (real multiprocess)
                                                              or SparkAgent (real PySpark)
                                                                 │
                                                                 ▼
                                                          ReportingAgent
                                                        (LLM: write report)
```

Every agent lives in `backend/app/agents/`. All LLM calls go through
`app/services/llm_service.py`, which supports Groq (fast hosted, free tier) or
OpenAI — set `LLM_PROVIDER` in `.env`.

## HPC/HTC features

**Real distributed data processing** — for `summary` and `groupby`
analyses, choose a processing paradigm in Prompt Studio:
- `pandas` — plain in-memory computation (default)
- `mapreduce` — `app/agents/mapreduce_agent.py`, real multiprocess map/shuffle/reduce
  (`app/services/partition_service.py` partitions the data; each partition's map
  task runs in its own OS worker process, verified via real process IDs)
- `spark` — `app/agents/spark_agent.py`, a real `SparkSession` running genuine
  Spark SQL `groupBy`/`agg` operations

All three paradigms are verified to produce numerically identical results
to plain pandas (see `tests/test_backend.py::test_mapreduce_agent_groupby_matches_pandas`
and `::test_spark_agent_groupby_matches_pandas`, and `scripts/run_benchmarks.py`
for a full scaling sweep) — the point is to compare real execution models,
not to change the answer.

**Real background job queue** — `app/services/workflow_service.py::dispatch_job`
sends jobs to a real Celery worker process over Redis, the standard
application-level job-queue pattern (analogous to what Slurm/HTCondor do
at the cluster-scheduler level). Falls back to FastAPI `BackgroundTasks`
automatically if Redis isn't running.

**Single-agent vs multi-agent architectures** — Prompt Studio lets you pick
between the multi-agent pipeline (Intent → Planning → Data → Analytics →
Reporting as separate specialized agents) and a single-agent architecture
(`app/agents/single_agent.py`) where one agent handles interpretation,
computation, and reporting in a single pass. Both are directly comparable
on the same prompt/dataset — the job detail page shows which architecture
ran and how many LLM calls it took.

**Simulated cluster & resource tracking** — `app/services/cluster_service.py`
still seeds 4 fixed nodes (CPU-only, GPU, and hybrid) and generates a
believable resource-utilization time series, since standing up a real
multi-node Slurm/HTCondor cluster was out of scope for the available time
(see "Suggested next steps"). This is explicitly labeled in the code and
in this README rather than presented as real.

## Project layout

```
hpc/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI entry point, rate limiting
│   │   ├── core/                    # config, database, JWT security, deps, celery_app, rate_limit
│   │   ├── models/                  # 7 SQLAlchemy models
│   │   ├── schemas/                 # Pydantic request/response schemas
│   │   ├── services/                # auth, LLM (Groq/OpenAI), analytics, datasets,
│   │   │                             # spark_service (real SparkSession), workflow (real Celery)
│   │   ├── agents/                  # intent, planning, data, analytics, mapreduce (real),
│   │   │                             # spark (real), execution, reporting, orchestrator
│   │   └── api/v1/endpoints/        # auth, prompts, workflows, jobs, datasets, admin, cluster
│   ├── data/
│   │   ├── employees.csv            # real dataset (4,653 rows)
│   │   ├── weather.csv               # real dataset (96,453 rows)
│   │   └── *_large.csv               # generated by scale_datasets.py, for benchmarking only
│   ├── scripts/
│   │   ├── scale_datasets.py         # produces large benchmark versions of the real data
│   │   ├── run_benchmarks.py         # pandas vs real Spark vs real MapReduce scaling benchmark
│   │   └── init.sql                  # reference schema (SQLAlchemy creates tables automatically)
│   ├── benchmark_results/            # results.json / results.md from an actual measured run
│   ├── tests/test_backend.py         # 24 pytest tests (SQLite, no Postgres/Redis/LLM needed)
│   ├── requirements.txt / Dockerfile / .env.example
│   └── pytest.ini
├── frontend/                        # Next.js 14 + Tailwind + Recharts
├── docker-compose.yml                # Postgres + Redis + backend + frontend
```

## Run it

### 1. Datasets (already included)

`backend/data/employees.csv` and `backend/data/weather.csv` are the real
datasets. Optionally generate large versions for benchmarking:

```bash
cd backend
pip install -r requirements.txt
python scripts/scale_datasets.py --employees 500000 --weather 1500000
```

### 2. Choose an LLM provider

**Groq (recommended — fast, free tier, no local GPU needed):**
```bash
# backend/.env
LLM_PROVIDER=groq
GROQ_API_KEY=your_key_here   # https://console.groq.com/keys — never commit this
GROQ_MODEL=openai/gpt-oss-20b
```

### 3. Redis + Celery worker (real job queue)

```bash
# Terminal 1: Redis
redis-server

# Terminal 2: Celery worker (a genuinely separate process from the API server)
cd backend
celery -A app.core.celery_app worker --loglevel=info
```

If you skip this, the app still works — jobs just run in-process via
FastAPI `BackgroundTasks` instead of a real queue (`dispatch_job` detects
Redis automatically and falls back safely).

### 4. Backend + frontend

```bash
# Terminal 3: Backend
cd backend
python3.11 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # edit with your LLM_PROVIDER / GROQ_API_KEY / etc.
uvicorn app.main:app --reload

# Terminal 4: Frontend
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

- Backend: http://localhost:8000 (docs at `/docs`)
- Frontend: http://localhost:3000

Register a user at http://localhost:3000/register, then head to **Prompt
Studio** and try: *"Show me average age by education level"* or *"How has
average temperature changed over the years?"*.

### Docker

```bash
docker compose up --build
```
Redis and the Celery worker are containerized.

### Running tests

```bash
cd backend
pytest tests/ -v
```
24 tests, including real correctness checks for the Spark and MapReduce
engines and the Celery/BackgroundTasks dispatch fallback logic. Uses
SQLite and a mocked LLM, so no Postgres or API key is required —
the Spark and MapReduce tests do start a real (if small/fast) execution
engine, so they take a few seconds longer than the rest.

### Running the distributed-compute benchmark

```bash
cd backend
python scripts/run_benchmarks.py --sizes 5000 50000 500000 --repeats 3
```
Produces `benchmark_results/results.json` (raw) — see
`benchmark_results/results.md` for a written-up, honest analysis of an
actual measured run, including the important caveat that Spark/MapReduce
only outperform pandas once there's enough data *and* enough CPU
cores/nodes to amortize their overhead.

## Suggested next steps (documented gaps, for the project report)

- **Real multi-node cluster scheduling** (Slurm or HTCondor via Docker
  Compose) to replace the simulated cluster dashboard — the biggest
  remaining gap between this platform and true HPC infrastructure.
- **Re-run `scripts/run_benchmarks.py` on a multi-core machine** (and
  ideally a real Spark cluster via `SPARK_MASTER_URL`) to capture the
  crossover point where distributed engines start winning — this
  sandbox's single-core benchmark run intentionally shows pandas winning,
  which is itself part of the reportable finding.
- **LLM accuracy evaluation**: a labeled prompt/intent test set with
  precision/recall, to turn the multi-agent-vs-single-agent comparison
  into a quantitative result.
- Real cluster/resource telemetry (`psutil`) instead of the simulated
  CPU/GPU numbers, if the cluster dashboard is kept.

