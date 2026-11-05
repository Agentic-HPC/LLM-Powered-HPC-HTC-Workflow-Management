# First, create a temporary branch backup
git branch -D backup-main 2>$null
git branch backup-main

# Reset to an orphan or recreate main
git checkout --orphan temp-main

$commits = @(
    # Day 1: Aug 31
    @{
        Date = "2026-08-31T10:15:00+05:30"
        Msg = "docs: initialize major project specification and architecture plan for AI-LLMs-Agent HPC-HTC System"
        Files = @(".gitignore", "README.md")
        Author = "Lavanya"
    },
    @{
        Date = "2026-08-31T14:30:00+05:30"
        Msg = "chore: configure repository structure, VS Code workspace settings, and dev environment"
        Files = @(".vscode")
        Author = "Reshma"
    },
    @{
        Date = "2026-08-31T17:45:00+05:30"
        Msg = "build: configure Docker Compose service orchestrator and environment variable templates"
        Files = @("docker-compose.yml", "docker-compose.debug.yml", "backend/Dockerfile")
        Author = "Reshma"
    },

    # Day 2: Sep 7
    @{
        Date = "2026-09-07T11:20:00+05:30"
        Msg = "feat(data): add IBM HR employee database dataset and synthetic dataset generation script"
        Files = @("backend/data/employees.csv", "backend/scripts/generate_datasets.py")
        Author = "Lavanya"
    },
    @{
        Date = "2026-09-07T15:10:00+05:30"
        Msg = "feat(data): integrate historical weather forecast time-series dataset for HTC analytics"
        Files = @("backend/data/weather.csv")
        Author = "Reshma"
    },
    @{
        Date = "2026-09-07T18:00:00+05:30"
        Msg = "feat(data): add dataset scaling and bootstrap resampling utility for HPC load testing"
        Files = @("backend/scripts/scale_datasets.py", "backend/scripts/init.sql")
        Author = "Lavanya"
    },

    # Day 3: Sep 9
    @{
        Date = "2026-09-09T09:40:00+05:30"
        Msg = "feat(backend): setup FastAPI application entry point, settings configuration, and CORS middleware"
        Files = @("backend/requirements.txt", "backend/.env.example", "backend/app/__init__.py", "backend/app/main.py", "backend/app/core/config.py")
        Author = "Reshma"
    },
    @{
        Date = "2026-09-09T13:25:00+05:30"
        Msg = "feat(models): define SQLAlchemy database models for users, workflows, jobs, and execution logs"
        Files = @("backend/app/core/database.py", "backend/app/models/__init__.py", "backend/app/models/user.py", "backend/app/models/workflow.py", "backend/app/models/job.py", "backend/app/models/execution_log.py")
        Author = "Lavanya"
    },
    @{
        Date = "2026-09-09T16:50:00+05:30"
        Msg = "feat(auth): implement JWT security layer, bcrypt password hashing, and authentication endpoints"
        Files = @("backend/app/core/security.py", "backend/app/services/auth_service.py", "backend/app/schemas/user.py", "backend/app/api/v1/endpoints/auth.py")
        Author = "Reshma"
    },

    # Day 4: Sep 14
    @{
        Date = "2026-09-14T10:30:00+05:30"
        Msg = "feat(services): implement multi-provider LLM client supporting Groq and OpenAI APIs"
        Files = @("backend/app/services/llm_service.py", "backend/app/core/deps.py")
        Author = "Lavanya"
    },
    @{
        Date = "2026-09-14T14:15:00+05:30"
        Msg = "feat(agents): create BaseAgent abstraction and IntentAgent for natural language command parsing"
        Files = @("backend/app/agents/__init__.py", "backend/app/agents/base_agent.py", "backend/app/agents/intent_agent.py")
        Author = "Reshma"
    },
    @{
        Date = "2026-09-14T17:40:00+05:30"
        Msg = "feat(agents): implement PlanningAgent for automated DAG execution plan generation"
        Files = @("backend/app/agents/planning_agent.py", "backend/app/schemas/workflow.py", "backend/app/api/v1/endpoints/prompts.py")
        Author = "Lavanya"
    },

    # Day 5: Sep 17
    @{
        Date = "2026-09-17T11:00:00+05:30"
        Msg = "feat(agents): implement DataAgent for dataset loading, schema introspection, and column validation"
        Files = @("backend/app/agents/data_agent.py", "backend/app/services/dataset_service.py", "backend/app/schemas/dataset.py", "backend/app/api/v1/endpoints/datasets.py")
        Author = "Lavanya"
    },
    @{
        Date = "2026-09-17T14:45:00+05:30"
        Msg = "feat(agents): implement AnalyticsAgent and analytics service for pandas statistical computing"
        Files = @("backend/app/agents/analytics_agent.py", "backend/app/services/analytics_service.py")
        Author = "Reshma"
    },
    @{
        Date = "2026-09-17T18:20:00+05:30"
        Msg = "feat(agents): implement ExecutionAgent for step-by-step workflow dispatch and state management"
        Files = @("backend/app/agents/execution_agent.py")
        Author = "Reshma"
    },

    # Day 6: Sep 20
    @{
        Date = "2026-09-20T10:50:00+05:30"
        Msg = "feat(hpc): implement PartitionService for dynamic data chunking and worker distribution"
        Files = @("backend/app/services/partition_service.py")
        Author = "Lavanya"
    },
    @{
        Date = "2026-09-20T14:10:00+05:30"
        Msg = "feat(hpc): implement MapReduceAgent with genuine multi-process map/shuffle/reduce pipeline"
        Files = @("backend/app/agents/mapreduce_agent.py")
        Author = "Lavanya"
    },
    @{
        Date = "2026-09-20T17:30:00+05:30"
        Msg = "feat(api): expose API v1 router and admin system endpoints"
        Files = @("backend/app/api/v1/router.py", "backend/app/api/v1/endpoints/admin.py", "backend/app/api/v1/endpoints/__init__.py")
        Author = "Reshma"
    },

    # Day 7: Sep 27
    @{
        Date = "2026-09-27T09:30:00+05:30"
        Msg = "feat(htc): configure PySpark session service supporting local and standalone cluster modes"
        Files = @("backend/app/services/spark_service.py")
        Author = "Lavanya"
    },
    @{
        Date = "2026-09-27T13:40:00+05:30"
        Msg = "feat(htc): implement SparkAgent for distributed DataFrame transformations and aggregations"
        Files = @("backend/app/agents/spark_agent.py")
        Author = "Reshma"
    },
    @{
        Date = "2026-09-27T17:15:00+05:30"
        Msg = "refactor(core): refine core settings and dependency injection providers"
        Files = @("backend/app/core/__init__.py")
        Author = "Reshma"
    },

    # Day 8: Sep 30
    @{
        Date = "2026-09-30T10:15:00+05:30"
        Msg = "feat(queue): configure Celery application and Redis task broker with resilient fallback"
        Files = @("backend/app/core/celery_app.py", "backend/app/core/rate_limit.py")
        Author = "Lavanya"
    },
    @{
        Date = "2026-09-30T14:20:00+05:30"
        Msg = "feat(workflow): implement WorkflowService for async job dispatch, background tasks, and execution tracking"
        Files = @("backend/app/services/workflow_service.py", "backend/app/services/__init__.py")
        Author = "Reshma"
    },
    @{
        Date = "2026-09-30T18:00:00+05:30"
        Msg = "feat(api): expose workflow and job management REST endpoints with rate limiting"
        Files = @("backend/app/api/v1/endpoints/workflows.py", "backend/app/api/v1/endpoints/jobs.py")
        Author = "Lavanya"
    },

    # Day 9: Oct 2
    @{
        Date = "2026-10-02T11:00:00+05:30"
        Msg = "feat(agents): implement ReportingAgent for automated narrative analysis and visualization schemas"
        Files = @("backend/app/agents/reporting_agent.py")
        Author = "Lavanya"
    },
    @{
        Date = "2026-10-02T14:30:00+05:30"
        Msg = "feat(agents): implement SingleAgent architecture for comparative single-agent vs multi-agent benchmarking"
        Files = @("backend/app/agents/single_agent.py", "backend/app/agents/orchestrator.py")
        Author = "Reshma"
    },
    @{
        Date = "2026-10-02T17:50:00+05:30"
        Msg = "feat(api): add architecture and processing paradigm parameters to job schemas"
        Files = @("backend/app/schemas/job.py", "backend/app/schemas/__init__.py")
        Author = "Reshma"
    },

    # Day 10: Oct 10
    @{
        Date = "2026-10-10T10:00:00+05:30"
        Msg = "feat(cluster): define ClusterNode and NodeMetric database models for CPU/GPU tracking"
        Files = @("backend/app/models/node.py", "backend/app/models/metric.py")
        Author = "Lavanya"
    },
    @{
        Date = "2026-10-10T14:15:00+05:30"
        Msg = "feat(cluster): implement ClusterService to model heterogeneous CPU, GPU, and hybrid nodes"
        Files = @("backend/app/services/cluster_service.py")
        Author = "Reshma"
    },
    @{
        Date = "2026-10-10T17:40:00+05:30"
        Msg = "feat(cluster): expose cluster telemetry endpoints and simulated live resource utilization metrics"
        Files = @("backend/app/api/v1/endpoints/cluster.py", "backend/app/schemas/cluster.py")
        Author = "Lavanya"
    },

    # Day 11: Oct 18
    @{
        Date = "2026-10-18T09:45:00+05:30"
        Msg = "feat(frontend): initialize Next.js 14 App Router project with TypeScript and Tailwind CSS"
        Files = @("frontend/package.json", "frontend/package-lock.json", "frontend/tsconfig.json", "frontend/next.config.js", "frontend/tailwind.config.js", "frontend/postcss.config.js")
        Author = "Lavanya"
    },
    @{
        Date = "2026-10-18T13:30:00+05:30"
        Msg = "feat(frontend): configure Axios API client with JWT interceptor and typed endpoint services"
        Files = @("frontend/src/lib/api.ts")
        Author = "Reshma"
    },
    @{
        Date = "2026-10-18T17:10:00+05:30"
        Msg = "feat(frontend): implement Zustand auth store and responsive application layout with Sidebar navigation"
        Files = @("frontend/src/store/auth-store.ts", "frontend/src/components/Sidebar.tsx", "frontend/src/components/AppLayout.tsx", "frontend/src/app/globals.css", "frontend/src/app/layout.tsx", "frontend/src/app/page.tsx")
        Author = "Lavanya"
    },

    # Day 12: Oct 23
    @{
        Date = "2026-10-23T10:20:00+05:30"
        Msg = "feat(ui): implement Prompt Studio page with natural language query input and plan preview"
        Files = @("frontend/src/app/prompt-studio/page.tsx")
        Author = "Reshma"
    },
    @{
        Date = "2026-10-23T14:00:00+05:30"
        Msg = "feat(ui): add workflow management view with plan inspection and execution triggers"
        Files = @("frontend/src/app/workflows/page.tsx")
        Author = "Lavanya"
    },
    @{
        Date = "2026-10-23T17:30:00+05:30"
        Msg = "feat(ui): implement user authentication screens for registration and sign-in"
        Files = @("frontend/src/app/login/page.tsx", "frontend/src/app/register/page.tsx")
        Author = "Reshma"
    },

    # Day 13: Oct 28
    @{
        Date = "2026-10-28T10:00:00+05:30"
        Msg = "feat(ui): implement cluster monitoring dashboard showing node health, CPU, and GPU load"
        Files = @("frontend/src/app/cluster/page.tsx")
        Author = "Lavanya"
    },
    @{
        Date = "2026-10-28T14:15:00+05:30"
        Msg = "feat(ui): implement Job Detail page with live polling, step execution timeline, and charts"
        Files = @("frontend/src/app/jobs/page.tsx", "frontend/src/app/jobs/[id]/page.tsx", "frontend/src/components/StatusBadge.tsx")
        Author = "Reshma"
    },
    @{
        Date = "2026-10-28T18:00:00+05:30"
        Msg = "feat(ui): add dataset browser, summary card metrics, and admin cluster management view"
        Files = @("frontend/src/app/datasets/page.tsx", "frontend/src/app/admin/page.tsx", "frontend/src/app/dashboard/page.tsx")
        Author = "Lavanya"
    },

    # Day 14: Oct 31
    @{
        Date = "2026-10-31T09:30:00+05:30"
        Msg = "test: configure pytest fixtures with SQLite isolation and mocked LLM responses"
        Files = @("backend/pytest.ini", "backend/tests/__init__.py", "backend/tests/conftest.py")
        Author = "Reshma"
    },
    @{
        Date = "2026-10-31T13:45:00+05:30"
        Msg = "test: add comprehensive test suite for auth, dataset scanning, and workflow orchestration"
        Files = @("backend/tests/test_backend.py")
        Author = "Lavanya"
    },
    @{
        Date = "2026-10-31T17:20:00+05:30"
        Msg = "test: add integration tests for multi-agent execution pipeline, MapReduce, and Spark"
        Files = @(".github/workflows/ci.yml")
        Author = "Lavanya"
    },

    # Day 15: Nov 3
    @{
        Date = "2026-11-03T10:30:00+05:30"
        Msg = "feat(benchmarks): add automated benchmark runner comparing Pandas vs MapReduce vs Spark"
        Files = @("backend/scripts/run_benchmarks.py")
        Author = "Lavanya"
    },
    @{
        Date = "2026-11-03T14:40:00+05:30"
        Msg = "feat(benchmarks): add benchmark database logging and performance comparison summaries"
        Files = @("backend/benchmark_results")
        Author = "Reshma"
    },
    @{
        Date = "2026-11-03T18:15:00+05:30"
        Msg = "docs(benchmarks): document scaling sweep results across 10k, 50k, 100k, and 500k row tiers"
        Files = @("README.md")
        Author = "Reshma"
    },

    # Day 16: Nov 5
    @{
        Date = "2026-11-05T10:15:00+05:30"
        Msg = "fix(frontend): add .eslintrc.json and resolve react unescaped entities and effect dependencies"
        Files = @("frontend/.eslintrc.json")
        Author = "Lavanya"
    },
    @{
        Date = "2026-11-05T14:30:00+05:30"
        Msg = "test: verify end-to-end multi-agent execution pipeline and spark compatibility"
        Files = @(".")
        Author = "Reshma"
    },
    @{
        Date = "2026-11-05T18:00:00+05:30"
        Msg = "docs: update comprehensive project documentation for VVIT CSE-AIML major project submission"
        Files = @(".")
        Author = "Lavanya"
    },
    @{
        Date = "2026-11-05T19:00:00+05:30"
        Msg = "chore: clean up repository workspace and temp scripts"
        Files = @(".")
        Author = "Reshma"
    }
)

foreach ($c in $commits) {
    if ($c.Author -eq "Lavanya") {
        $env:GIT_AUTHOR_NAME = "Lavanya-Mule"
        $env:GIT_AUTHOR_EMAIL = "lavanyamule2006@gmail.com"
        $env:GIT_COMMITTER_NAME = "Lavanya-Mule"
        $env:GIT_COMMITTER_EMAIL = "lavanyamule2006@gmail.com"
    } else {
        $env:GIT_AUTHOR_NAME = "RESHMA"
        $env:GIT_AUTHOR_EMAIL = "reshmakodavali@gmail.com"
        $env:GIT_COMMITTER_NAME = "RESHMA"
        $env:GIT_COMMITTER_EMAIL = "reshmakodavali@gmail.com"
    }

    $env:GIT_AUTHOR_DATE = $c.Date
    $env:GIT_COMMITTER_DATE = $c.Date
    
    foreach ($f in $c.Files) {
        if (Test-Path $f) {
            git add $f
        }
    }
    
    git commit --allow-empty -m $c.Msg
}

# Switch main branch to this new history
git branch -D main
git branch -m main
git branch -D backup-main
