from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from app.models.observation import Observation, OpsEvent, ZeroResultCluster  # noqa: F401

    Base.metadata.create_all(bind=engine)
    ensure_ops_events_ingested_at()


def ensure_ops_events_ingested_at():
    inspector = inspect(engine)
    if "ops_events" not in inspector.get_table_names():
        return
    column_names = {column["name"] for column in inspector.get_columns("ops_events")}
    if "ingested_at" in column_names:
        return

    if engine.dialect.name == "postgresql":
        statement = "ALTER TABLE ops_events ADD COLUMN ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW()"
    else:
        statement = "ALTER TABLE ops_events ADD COLUMN ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
    with engine.begin() as connection:
        connection.execute(text(statement))
