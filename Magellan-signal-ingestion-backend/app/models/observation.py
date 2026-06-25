from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text, JSON
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


class Product(Base):

    __tablename__ = "products"

    id = Column(String, primary_key=True, index=True)

    category = Column(String, nullable=False, index=True)

    payload = Column(JsonDocument, nullable=False)

    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class MerchandisingRule(Base):

    __tablename__ = "rules"

    rule_id = Column(String, primary_key=True, index=True)

    rule_type = Column(String, nullable=False, index=True)

    active = Column(Boolean, default=True, nullable=False, index=True)

    payload = Column(JsonDocument, nullable=False)

    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class SearchLog(Base):

    __tablename__ = "search_logs"

    id = Column(Integer, primary_key=True, index=True)

    request_id = Column(String, unique=True, nullable=False, index=True)

    session_id = Column(String, index=True)

    tenant = Column(String, nullable=False, index=True)

    source = Column(String, nullable=False)

    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)

    query_text = Column(String, nullable=False)

    normalized_query = Column(String)

    status_code = Column(Integer, nullable=False)

    latency_ms = Column(Integer, nullable=False)

    result_count = Column(Integer, nullable=False)

    click_count = Column(Integer, default=0)

    cart_add_count = Column(Integer, default=0)

    has_error = Column(Boolean, default=False)

    payload = Column(JsonDocument, nullable=False)

    ingested_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class TenantConfig(Base):

    __tablename__ = "tenant_configs"

    tenant = Column(String, primary_key=True, index=True)

    config_payload = Column(JsonDocument, nullable=False)

    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class TenantMetricBaseline(Base):

    __tablename__ = "tenant_metric_baselines"

    id = Column(Integer, primary_key=True, index=True)

    tenant = Column(String, index=True, nullable=False)

    metric_name = Column(String, index=True, nullable=False)

    ewma_value = Column(Float, nullable=False, default=0.0)

    ewma_variance = Column(Float, nullable=False, default=0.0)

    sample_count = Column(Integer, nullable=False, default=0)

    last_updated = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class SnapshotState(Base):

    __tablename__ = "snapshot_states"

    tenant = Column(String, primary_key=True, index=True)

    snapshot_type = Column(String, primary_key=True, index=True)

    payload = Column(JsonDocument, nullable=False)

    last_updated = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
