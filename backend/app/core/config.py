"""
Application configuration, loaded from environment variables (.env).
"""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- App ---
    APP_NAME: str = "HPC/HTC AI Platform"
    ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # --- Security ---
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    # Rate limiting (slowapi/limits syntax, e.g. "100/minute"). Applies
    # globally by default; the LLM-calling prompt endpoint and job-creation
    # endpoint (which can spin up a real Spark job) use a stricter limit -
    # see app/api/v1/endpoints/prompts.py and jobs.py.
    RATE_LIMIT_DEFAULT: str = "100/minute"
    RATE_LIMIT_EXPENSIVE: str = "10/minute"

    # --- Database ---
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/hpc_platform"

    # --- Redis / job queue ---
    REDIS_URL: str = "redis://localhost:6379/0"
    # "celery" (real background worker process, requires a running Celery
    # worker + reachable Redis) or "background_tasks" (in-process fallback,
    # used automatically by tests and when Redis isn't reachable).
    JOB_QUEUE_BACKEND: str = "celery"

    # --- CORS ---
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # --- LLM Provider selection ---
    # "groq" (default, hosted) or "openai" (hosted)
    LLM_PROVIDER: str = "groq"

    # --- OpenAI fallback (optional) ---
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # --- Dataset paths ---
    DATASET_DIR: str = "data"

    # --- Real Apache Spark (replaces earlier simulated engine) ---
    # "local[*]" runs a genuine single-machine Spark engine using every
    # core available. Point this at a real standalone/YARN/K8s cluster
    # (e.g. "spark://spark-master:7077") to run on real multi-node HPC
    # infrastructure with zero code changes.
    SPARK_MASTER_URL: str = "local[*]"
    SPARK_DRIVER_MEMORY: str = "2g"
    SPARK_SHUFFLE_PARTITIONS: int = 8

    # --- Real multiprocessing MapReduce ---
    # Number of OS worker processes used for the (now genuinely parallel,
    # not simulated) MapReduceAgent. Defaults to all cores.
    MAPREDUCE_MAX_WORKERS: int = 0  # 0 = os.cpu_count()

    # --- Groq (fast, free-tier-friendly cloud LLM provider) ---
    GROQ_API_KEY: str = ""
    # Groq's model catalog changes over time - some older "flagship" models
    # (e.g. llama-3.1-8b-instant, llama-3.3-70b-versatile) have moved to
    # Enterprise-only access. openai/gpt-oss-20b is, as of this writing,
    # on Groq's freely-available Production Models list. If you get a 404
    # "model does not exist or you do not have access to it" error, run
    # `curl https://api.groq.com/openai/v1/models -H "Authorization: Bearer $GROQ_API_KEY"`
    # to see what your key can actually use, and update this setting.
    GROQ_MODEL: str = "openai/gpt-oss-20b"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
