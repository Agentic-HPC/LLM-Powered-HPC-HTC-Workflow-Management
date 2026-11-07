"""
SQLAlchemy engine, session factory, and declarative base.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a database session and closes it after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables. Used for local/dev bootstrapping and tests."""
    import app.models  # noqa: F401 ensures all models are registered on Base
    Base.metadata.create_all(bind=engine)
    ensure_schema_migrations()


def ensure_schema_migrations():
    """Ensure database schema is compatible with latest model changes (e.g. prompt on jobs)."""
    from sqlalchemy import text
    with engine.connect() as conn:
        try:
            # Check if 'prompt' column exists in 'jobs' table
            if settings.DATABASE_URL.startswith("sqlite"):
                cols = [row[1] for row in conn.execute(text("PRAGMA table_info(jobs)")).fetchall()]
                if cols and "prompt" not in cols:
                    conn.execute(text("ALTER TABLE jobs ADD COLUMN prompt TEXT"))
                    conn.commit()
            elif settings.DATABASE_URL.startswith("postgres"):
                res = conn.execute(text(
                    "SELECT column_name FROM information_schema.columns WHERE table_name='jobs' AND column_name='prompt'"
                )).fetchone()
                if not res:
                    conn.execute(text("ALTER TABLE jobs ADD COLUMN prompt TEXT"))
                    conn.commit()
        except Exception:
            pass  # Table might not exist yet or migration already applied
