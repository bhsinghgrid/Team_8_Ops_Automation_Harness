from datetime import datetime
from typing import Any, Dict, List

from app.schemas.detected_signal import DetectedSignal
from app.schemas.search_log_schema import SearchLogEntry
from app.services.detectors.base import BaseDetector


from sqlalchemy.orm import Session
from app.utils.adaptive_thresholds import evaluate_adaptive_metric

class ErrorDetector(BaseDetector):

    def detect(
        self,
        logs: List[SearchLogEntry],
        window_start: datetime,
        window_end: datetime,
        db: Session = None,
    ) -> List[DetectedSignal]:
        total_count = len(logs)

        min_sample = self.config.get("min_sample_size", 10)
        if total_count < min_sample:
            return []

        error_logs = [
            log for log in logs 
            if log.response.status_code >= 400 or log.error is not None
        ]
        error_count = len(error_logs)
        error_rate = error_count / total_count

        warning_thresh = self.config.get("rate_warning", 0.01)
        critical_thresh = self.config.get("rate_critical", 0.05)

        is_adaptive = self.config.get("adaptive_mode", False)
        severity = None
        summary = ""
        evidence_dict = {
            "error_count": error_count,
            "sample_size": total_count,
            "error_rate": error_rate,
        }

        if is_adaptive and db:
            tenant = logs[0].tenant
            z_score, baseline_val = evaluate_adaptive_metric(
                db=db, tenant=tenant, metric_name="error_rate", current_value=error_rate
            )
            warning_z = self.config.get("adaptive_warning_z", 2.0)
            critical_z = self.config.get("adaptive_critical_z", 3.0)
            
            evidence_dict.update({
                "adaptive_mode": True,
                "z_score": z_score,
                "baseline_rate": baseline_val
            })

            # Check positive deviation (error rate got higher)
            if z_score > critical_z:
                severity = "critical"
                summary = f"Error rate of {error_rate * 100:.1f}% is highly anomalous (Z={z_score:.1f}, baseline={baseline_val * 100:.1f}%)"
            elif z_score > warning_z:
                severity = "warning"
                summary = f"Error rate of {error_rate * 100:.1f}% is anomalous (Z={z_score:.1f}, baseline={baseline_val * 100:.1f}%)"
        else:
            if error_rate > critical_thresh:
                severity = "critical"
            elif error_rate > warning_thresh:
                severity = "warning"
                
            if severity:
                summary = f"Error rate of {error_rate * 100:.1f}% exceeded threshold of {warning_thresh * 100 if severity == 'warning' else critical_thresh * 100:.1f}%"
                
            evidence_dict.update({
                "warning_threshold_rate": warning_thresh,
                "critical_threshold_rate": critical_thresh,
            })

        if severity:
            error_queries = list({log.query.text for log in error_logs})
            tenant = logs[0].tenant if logs else "unknown"

            return [
                DetectedSignal(
                    signal_type="error_rate",
                    tenant=tenant,
                    severity=severity,
                    summary=summary,
                    evidence=evidence_dict,
                    affected_queries=error_queries,
                    window_start=window_start,
                    window_end=window_end,
                )
            ]

        return []
