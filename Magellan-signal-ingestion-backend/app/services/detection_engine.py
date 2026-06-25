import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.detection_config import DETECTION_DEFAULTS
from app.models.observation import OpsEvent, SearchLog
from app.schemas.detected_signal import DetectedSignal
from app.schemas.search_log_schema import SearchLogEntry
from app.services.detectors.base import BaseDetector
from app.services.detectors.latency_detector import LatencyDetector
from app.services.detectors.zero_result_detector import ZeroResultDetector
from app.services.detectors.ctr_detector import CtrDetector
from app.services.detectors.error_detector import ErrorDetector
from app.services.detectors.relevance_detector import RelevanceDetector

logger = logging.getLogger(__name__)


class DetectionEngine:

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or DETECTION_DEFAULTS
        
        # Initialize and register detectors with configured thresholds
        self.detectors: List[BaseDetector] = [
            LatencyDetector(self.config.get("latency_spike")),
            ZeroResultDetector(self.config.get("zero_results")),
            CtrDetector(self.config.get("low_ctr")),
            ErrorDetector(self.config.get("error_rate")),
            RelevanceDetector(self.config.get("relevance_drift")),
        ]

    def run(self, logs: List[SearchLogEntry], window_minutes: int = 5, db: Session = None) -> List[DetectedSignal]:
        """
        Groups logs into tumbling time windows and executes all registered detectors.
        """
        if not logs:
            return []

        # Sort logs chronologically
        sorted_logs = sorted(logs, key=lambda l: l.timestamp)

        # Build time-based tumbling windows
        window_duration = timedelta(minutes=window_minutes)
        first_ts = sorted_logs[0].timestamp
        
        # Stable window starting minute
        start_minute = (first_ts.minute // window_minutes) * window_minutes
        window_start = first_ts.replace(minute=start_minute, second=0, microsecond=0)

        windows = []
        current_window_start = window_start
        current_window_logs = []

        for log in sorted_logs:
            while log.timestamp >= current_window_start + window_duration:
                if current_window_logs:
                    windows.append((
                        current_window_start,
                        current_window_start + window_duration,
                        current_window_logs
                    ))
                    current_window_logs = []
                current_window_start += window_duration
            current_window_logs.append(log)

        if current_window_logs:
            windows.append((
                current_window_start,
                current_window_start + window_duration,
                current_window_logs
            ))

        # Run registered detectors on each window
        detected_signals = []
        for w_start, w_end, w_logs in windows:
            for detector in self.detectors:
                try:
                    signals = detector.detect(w_logs, w_start, w_end, db=db)
                    detected_signals.extend(signals)
                except Exception as e:
                    logger.exception(
                        "Error running detector %s on window %s - %s",
                        detector.__class__.__name__, w_start, w_end
                    )

        return detected_signals

    def persist_signals(self, db: Session, signals: List[DetectedSignal]) -> List[OpsEvent]:
        """
        Converts detected signals into OpsEvent models and saves them to the database.
        """
        events = []
        for sig in signals:
            event_id = f"SIG-{sig.window_end:%Y%m%d}-{uuid.uuid4().hex[:8]}"
            
            event = OpsEvent(
                event_id=event_id,
                event_type="passive_signal",
                source_capability="semantic_search",
                severity=sig.severity,
                timestamp=sig.window_end,
                provider="gd_ai_search",
                tenant=sig.tenant,
                payload=sig.model_dump(mode='json'),
            )
            try:
                db.add(event)
                db.commit()
                db.refresh(event)
                events.append(event)
            except IntegrityError:
                db.rollback()
                logger.warning("OpsEvent with event_id %s already exists. Skipping.", event_id)
                continue
        return events

    def persist_raw_logs(self, db: Session, logs: List[SearchLogEntry]) -> int:
        """
        Saves raw log entries to the search_logs table. Returns the count of newly inserted logs.
        """
        inserted = 0
        for entry in logs:
            existing = db.query(SearchLog).filter(SearchLog.request_id == entry.request_id).first()
            if existing:
                continue

            click_count = len(entry.interaction.clicks)
            cart_add_count = len(entry.interaction.cart_adds)
            has_error = (entry.error is not None or entry.response.status_code >= 400)

            db_log = SearchLog(
                request_id=entry.request_id,
                session_id=entry.session_id,
                tenant=entry.tenant,
                source=entry.source,
                timestamp=entry.timestamp,
                query_text=entry.query.text,
                normalized_query=entry.query.normalized_text,
                status_code=entry.response.status_code,
                latency_ms=entry.response.latency_ms,
                result_count=entry.response.result_count,
                click_count=click_count,
                cart_add_count=cart_add_count,
                has_error=has_error,
                payload=entry.model_dump(mode='json')
            )
            db.add(db_log)
            inserted += 1

        if inserted > 0:
            try:
                db.commit()
            except Exception as e:
                db.rollback()
                logger.error("Error committing raw search logs to database: %s", str(e))
                return 0
        return inserted
