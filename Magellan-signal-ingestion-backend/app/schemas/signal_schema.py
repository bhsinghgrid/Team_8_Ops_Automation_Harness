from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

EventType = Literal["search_result", "catalog_delta", "rule_diff"]
Severity = Literal["critical", "warning", "info"]
SourceCapability = Literal["semantic_search", "catalog", "mxp_merchandising"]
ProviderName = Literal["ocs", "manual"]


class SearchSignalRequest(BaseModel):

    query_id: Optional[str] = None
    query_text: str = Field(..., min_length=1)
    tenant: Optional[str] = None
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    filters: Dict[str, Any] = Field(default_factory=dict)
    sort: Optional[str] = None


class BatchSearchRequest(BaseModel):

    queries_file: str = "mock-data/queries/benchmark_queries.json"
    tenant: Optional[str] = None
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class CatalogDeltaRequest(BaseModel):

    product_id: str = Field(..., min_length=1)
    operation: Literal["INSERT", "UPDATE", "DELETE"]
    changed_fields: List[str] = Field(default_factory=list)
    before: Dict[str, Any] = Field(default_factory=dict)
    after: Dict[str, Any] = Field(default_factory=dict)
    missing_attributes: List[str] = Field(default_factory=list)


class CatalogDiffRequest(BaseModel):

    product_id: str = Field(..., min_length=1)
    operation: Literal["INSERT", "UPDATE", "DELETE"]
    changed_fields: List[str] = Field(default_factory=list)
    before: Optional[Dict[str, Any]] = None
    after: Optional[Dict[str, Any]] = None
    missing_attributes: List[str] = Field(default_factory=list)


class CatalogDiffResponse(BaseModel):

    event_id: str
    severity: Severity
    event_type: EventType = "catalog_delta"
    message: str


class RuleDiffRequest(BaseModel):

    rule_id: str = Field(..., min_length=1)
    rule_type: Literal["boost", "suppress", "synonym"]
    operation: Literal["INSERT", "UPDATE", "DELETE"]
    changed_fields: List[str] = Field(default_factory=list)
    before_state: Optional[Dict[str, Any]] = None
    after_state: Optional[Dict[str, Any]] = None
    author: str = Field(..., min_length=1)
    oos_conflicts: List[Dict[str, Any]] = Field(default_factory=list)


class RuleDiffResponse(BaseModel):

    event_id: str
    severity: Severity
    event_type: EventType = "rule_diff"
    message: str


class OpsEventResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    event_id: str
    event_type: EventType
    source_capability: SourceCapability
    severity: Severity
    timestamp: datetime
    provider: ProviderName
    tenant: str
    payload: Dict[str, Any]
    created: bool = True


class SearchBatchResponse(BaseModel):

    total: int
    succeeded: int
    failed: int
    zero_result_count: int
    event_ids: List[str]
    errors: List[Dict[str, Any]] = Field(default_factory=list)


class ZeroResultClusterResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: int
    cluster_intent: str
    query_examples: List[str]
    hit_count: int
    first_seen: datetime
    last_seen: datetime
    status: Literal["open", "acknowledged", "resolved"]
    recommended_runbook: Optional[Literal["catalog_qa_agent", "index_refresh"]] = None
