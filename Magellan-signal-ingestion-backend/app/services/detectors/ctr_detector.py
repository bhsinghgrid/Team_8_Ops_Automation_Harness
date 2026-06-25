from datetime import datetime
from typing import Any, Dict, List

from app.schemas.detected_signal import DetectedSignal
from app.schemas.search_log_schema import SearchLogEntry
from app.services.detectors.base import BaseDetector


from sqlalchemy.orm import Session
from app.utils.adaptive_thresholds import evaluate_adaptive_metric

class CtrDetector(BaseDetector):

    def detect(
        self,
        logs: List[SearchLogEntry],
        window_start: datetime,
        window_end: datetime,
        db: Session = None,
    ) -> List[DetectedSignal]:
        eligible_logs = [
            log for log in logs 
            if log.response.status_code == 200 and log.response.result_count > 0
        ]
        total_count = len(eligible_logs)

        min_sample = self.config.get("min_sample_size", 20)
        if total_count < min_sample:
            return []

        clicked_logs = [log for log in eligible_logs if len(log.interaction.clicks) > 0]
        clicked_count = len(clicked_logs)
        ctr = clicked_count / total_count

        warning_thresh = self.config.get("rate_warning", 0.05)
        critical_thresh = self.config.get("rate_critical", 0.02)

        is_adaptive = self.config.get("adaptive_mode", False)
        severity = None
        summary = ""
        evidence_dict = {
            "clicked_search_count": clicked_count,
            "sample_size": total_count,
            "ctr": ctr,
        }

        if is_adaptive and db:
            tenant = logs[0].tenant
            z_score, baseline_val = evaluate_adaptive_metric(
                db=db, tenant=tenant, metric_name="ctr", current_value=ctr
            )
            # CTR we want negative z-score (drops)
            warning_z = self.config.get("adaptive_warning_z", 2.0)
            critical_z = self.config.get("adaptive_critical_z", 3.0)
            
            evidence_dict.update({
                "adaptive_mode": True,
                "z_score": z_score,
                "baseline_ctr": baseline_val
            })

            # Negative deviation (CTR dropped)
            if z_score < -critical_z:
                severity = "critical"
                summary = f"CTR of {ctr * 100:.1f}% is highly anomalous (Z={z_score:.1f}, baseline={baseline_val * 100:.1f}%)"
            elif z_score < -warning_z:
                severity = "warning"
                summary = f"CTR of {ctr * 100:.1f}% is anomalous (Z={z_score:.1f}, baseline={baseline_val * 100:.1f}%)"
        else:
            if ctr < critical_thresh:
                severity = "critical"
            elif ctr < warning_thresh:
                severity = "warning"
                
            if severity:
                summary = f"CTR of {ctr * 100:.1f}% fell below threshold of {warning_thresh * 100 if severity == 'warning' else critical_thresh * 100:.1f}%"
                
            evidence_dict.update({
                "warning_threshold_ctr": warning_thresh,
                "critical_threshold_ctr": critical_thresh,
            })

        if severity:
            no_click_queries = list({
                log.query.text 
                for log in eligible_logs 
                if len(log.interaction.clicks) == 0
            })
            tenant = logs[0].tenant if logs else "unknown"

            return [
                DetectedSignal(
                    signal_type="low_ctr",
                    tenant=tenant,
                    severity=severity,
                    summary=summary,
                    evidence=evidence_dict,
                    affected_queries=no_click_queries,
                    window_start=window_start,
                    window_end=window_end,
                )
            ]

        return []
