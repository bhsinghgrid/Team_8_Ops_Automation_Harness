from pydantic import BaseModel
from typing import List, Optional


class ObservationResponse(BaseModel):

    query_id: str

    query_text: str

    status_code: int

    latency_ms: int

    result_count: int

    top_product_ids: Optional[List[str]]

    source: str
