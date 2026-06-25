from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List

from app.schemas.detected_signal import DetectedSignal
from app.schemas.search_log_schema import SearchLogEntry


from sqlalchemy.orm import Session

class BaseDetector(ABC):

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

    @abstractmethod
    def detect(
        self,
        logs: List[SearchLogEntry],
        window_start: datetime,
        window_end: datetime,
        db: Session = None,
    ) -> List[DetectedSignal]:
        """Consumes a list of logs and generates a list of detected signals, if any."""
        pass
