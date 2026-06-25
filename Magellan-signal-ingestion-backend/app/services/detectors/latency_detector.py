from datetime import datetime
from typing import Any, Dict, List

from app.schemas.detected_signal import DetectedSignal
from app.schemas.search_log_schema import SearchLogEntry
from app.services.detectors.base import BaseDetector


from sqlalchemy.orm import Session
from app.utils.adaptive_thresholds import evaluate_adaptive_metric

class LatencyDetector(BaseDetector):

    def detect(
        self,
        logs: List[SearchLogEntry],
        window_start: datetime,
        window_end: datetime,
        db: Session = None,
    ) -> List[DetectedSignal]:
        if not logs:
            return []

        latencies = [log.response.latency_ms for log in logs]
        if not latencies:
            return []

        sorted_lats = sorted(latencies)
        p95_index = int(len(sorted_lats) * 0.95)
        if p95_index >= len(sorted_lats):
            p95_index = len(sorted_lats) - 1
        p95_latency = sorted_lats[p95_index]

        warning_thresh = self.config.get("p95_warning_ms", 500)
        critical_thresh = self.config.get("p95_critical_ms", 1000)

        is_adaptive = self.config.get("adaptive_mode", False)
        severity = None
        summary = ""
        evidence_dict = {
            "p95_latency_ms": p95_latency,
            "sample_size": len(logs),
        }

        if is_adaptive and db:
            tenant = logs[0].tenant
            z_score, baseline_val = evaluate_adaptive_metric(
                db=db, tenant=tenant, metric_name="latency_p95", current_value=p95_latency
            )
            warning_z = self.config.get("adaptive_warning_z", 2.0)
            critical_z = self.config.get("adaptive_critical_z", 3.0)
            
            evidence_dict.update({
                "adaptive_mode": True,
                "z_score": z_score,
                "baseline_p95": baseline_val
            })

            # Check positive deviation (latency got higher)
            if z_score > critical_z:
                severity = "critical"
                summary = f"P95 latency of {p95_latency}ms is highly anomalous (Z={z_score:.1f}, baseline={baseline_val:.1f}ms)"
            elif z_score > warning_z:
                severity = "warning"
                summary = f"P95 latency of {p95_latency}ms is anomalous (Z={z_score:.1f}, baseline={baseline_val:.1f}ms)"
        else:
            # Static logic fallback
            if p95_latency > critical_thresh:
                severity = "critical"
            elif p95_latency > warning_thresh:
                severity = "warning"
            
            if severity:
                summary = f"P95 latency of {p95_latency}ms exceeded threshold of {warning_thresh if severity == 'warning' else critical_thresh}ms"
            
            evidence_dict.update({
                "warning_threshold_ms": warning_thresh,
                "critical_threshold_ms": critical_thresh,
            })

        if severity:
            slow_queries = list({
                log.query.text
                for log in logs
                if log.response.latency_ms > warning_thresh
            })
            tenant = logs[0].tenant if logs else "unknown"

            return [
                DetectedSignal(
                    signal_type="latency_spike",
                    tenant=tenant,
                    severity=severity,
                    summary=summary,
                    evidence=evidence_dict,
                    affected_queries=slow_queries,
                    window_start=window_start,
                    window_end=window_end,
                )
            ]

        return []
