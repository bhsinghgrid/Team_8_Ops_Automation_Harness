from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class QueryBlock(BaseModel):
    text: str = Field(..., description="Raw search query text entered by the user.")
    normalized_text: Optional[str] = Field(None, description="Normalized version of the query text.")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Key-value filters applied to the query.")
    sort: Optional[str] = Field(None, description="The sort order applied to the search results.")


class ResultItem(BaseModel):
    product_id: str = Field(..., description="Unique identifier of the returned product.")
    rank: int = Field(..., description="1-based rank of the product in the search results.")
    score: float = Field(..., description="Relevance score assigned to the product.")


class ResponseBlock(BaseModel):
    status_code: int = Field(..., description="HTTP status code of the search response.")
    latency_ms: int = Field(..., description="Latency of the search request in milliseconds.")
    result_count: int = Field(..., description="Total number of results matching the search query.")
    results: List[ResultItem] = Field(default_factory=list, description="Ordered list of search results returned to the user.")


class ClickEvent(BaseModel):
    product_id: str = Field(..., description="Unique identifier of the clicked product.")
    rank: int = Field(..., description="Rank of the product when clicked.")
    timestamp: datetime = Field(..., description="Timestamp of the click event.")


class InteractionBlock(BaseModel):
    clicks: List[ClickEvent] = Field(default_factory=list, description="List of click interactions.")
    cart_adds: List[ClickEvent] = Field(default_factory=list, description="List of cart add interactions.")


class ContextBlock(BaseModel):
    device_type: str = Field(..., description="The device type used for search.")
    channel: str = Field(..., description="The sales/interaction channel.")
    locale: str = Field(..., description="The locale of the search event.")


class SearchLogEntry(BaseModel):
    timestamp: datetime = Field(..., description="ISO 8601 formatted timestamp of the search request.")
    source: str = Field(..., description="The log source / search platform provider.")
    tenant: str = Field(..., description="Identifier for the retail tenant.")
    request_id: str = Field(..., description="Unique identifier for the search request.")
    session_id: str = Field(..., description="Unique identifier for the user session.")
    user_id_hash: str = Field(..., description="Anonymized hash of the user identifier.")
    query: QueryBlock = Field(..., description="Contains details about the search query.")
    response: ResponseBlock = Field(..., description="Contains details about the search response.")
    interaction: InteractionBlock = Field(..., description="Contains post-search interactions.")
    context: ContextBlock = Field(..., description="Metadata context surrounding the search event.")
    error: Optional[str] = Field(None, description="Error message or code if the search request failed.")


class SearchLogBatchRequest(BaseModel):
    logs: List[SearchLogEntry]
