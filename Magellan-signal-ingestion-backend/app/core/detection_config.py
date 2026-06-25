DETECTION_DEFAULTS = {
    "latency_spike": {
        "p95_warning_ms": 500,
        "p95_critical_ms": 1000,
        "window_minutes": 5,
        "adaptive_mode": False,
        "adaptive_warning_z": 2.0,
        "adaptive_critical_z": 3.0,
    },
    "zero_results": {
        "rate_warning": 0.10,
        "rate_critical": 0.25,
        "min_sample_size": 10,
        "adaptive_mode": False,
        "adaptive_warning_z": 2.0,
        "adaptive_critical_z": 3.0,
    },
    "low_ctr": {
        "rate_warning": 0.05,
        "rate_critical": 0.02,
        "min_sample_size": 20,
        "adaptive_mode": False,
        "adaptive_warning_z": 2.0,
        "adaptive_critical_z": 3.0,
    },
    "error_rate": {
        "rate_warning": 0.01,
        "rate_critical": 0.05,
        "min_sample_size": 10,
        "adaptive_mode": False,
        "adaptive_warning_z": 2.0,
        "adaptive_critical_z": 3.0,
    },
    "relevance_drift": {
        "avg_score_warning": 0.5,
        "avg_score_critical": 0.3,
        "min_sample_size": 10,
    },
}
