from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String, Text, JSON
from sqlalchemy.dialects.postgresql import JSONB

from app.db.database import Base

JsonDocument = JSON().with_variant(JSONB, "postgresql")


class Observation(Base):

    __tablename__ = "observations"

    id = Column(Integer, primary_key=True, index=True)

    query_id = Column(String)

    query_text = Column(String)

    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    status_code = Column(Integer)

    latency_ms = Column(Integer)

    result_count = Column(Integer)

    top_product_ids = Column(JSON)

    response_payload = Column(JSON)

    source = Column(String)


class OpsEvent(Base):

    __tablename__ = "ops_events"

    id = Column(Integer, primary_key=True, index=True)

    event_id = Column(Text, unique=True, nullable=False, index=True)

    event_type = Column(String, nullable=False, index=True)

    source_capability = Column(String, nullable=False, index=True)

    severity = Column(String, nullable=False, index=True)

    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    provider = Column(String, nullable=False)

    tenant = Column(String, nullable=False, index=True)

    payload = Column(JsonDocument, nullable=False)

    ingested_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class ZeroResultCluster(Base):

    __tablename__ = "zero_result_clusters"

    id = Column(Integer, primary_key=True, index=True)

    cluster_intent = Column(Text, unique=True, nullable=False, index=True)

    query_examples = Column(JsonDocument, nullable=False, default=list)

    hit_count = Column(Integer, default=1, nullable=False)

    first_seen = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    last_seen = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    status = Column(String, default="open", nullable=False)

    recommended_runbook = Column(String)
