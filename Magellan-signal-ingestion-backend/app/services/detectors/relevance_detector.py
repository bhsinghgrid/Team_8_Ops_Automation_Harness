from datetime import datetime
from typing import Any, Dict, List

from app.schemas.detected_signal import DetectedSignal
from app.schemas.search_log_schema import SearchLogEntry
from app.services.detectors.base import BaseDetector


class RelevanceDetector(BaseDetector):

    def detect(
        self,
        logs: List[SearchLogEntry],
        window_start: datetime,
        window_end: datetime,
    ) -> List[DetectedSignal]:
        # Filter to successful searches that actually returned results
        eligible_logs = [
            log for log in logs 
            if log.response.status_code == 200 and log.response.result_count > 0 and log.response.results
        ]
        total_count = len(eligible_logs)

        min_sample = self.config.get("min_sample_size", 10)
        if total_count < min_sample:
            return []

        # Calculate average result score for each search event
        log_avg_scores = []
        low_relevance_queries = []
        warning_thresh = self.config.get("avg_score_warning", 0.5)

        for log in eligible_logs:
            scores = [r.score for r in log.response.results]
            avg_score = sum(scores) / len(scores) if scores else 0.0
            log_avg_scores.append(avg_score)
            if avg_score < warning_thresh:
                low_relevance_queries.append(log.query.text)

        mean_avg_score = sum(log_avg_scores) / total_count if log_avg_scores else 0.0

        critical_thresh = self.config.get("avg_score_critical", 0.3)

        severity = None
        if mean_avg_score < critical_thresh:
            severity = "critical"
        elif mean_avg_score < warning_thresh:
            severity = "warning"

        if severity:
            summary = f"Mean top-result relevance score of {mean_avg_score:.2f} fell below threshold of {warning_thresh if severity == 'warning' else critical_thresh}"
            tenant = logs[0].tenant if logs else "unknown"

            return [
                DetectedSignal(
                    signal_type="relevance_drift",
                    tenant=tenant,
                    severity=severity,
                    summary=summary,
                    evidence={
                        "mean_average_score": mean_avg_score,
                        "sample_size": total_count,
                        "warning_threshold_score": warning_thresh,
                        "critical_threshold_score": critical_thresh,
                    },
                    affected_queries=low_relevance_queries,
                    window_start=window_start,
                    window_end=window_end,
                )
            ]

        return []
