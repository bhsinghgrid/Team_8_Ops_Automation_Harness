"""
Traffic Mirror — decides which requests get shadowed.
"""

import random
import logging
from typing import Optional

from shadow_agent_framework.config.settings import ShadowTestConfig
from ..models.schemas import InferenceRequest

logger = logging.getLogger(__name__)


class TrafficMirror:
    """
    Controls which production requests are mirrored to challenger models.
    
    Uses configurable sampling rate to determine if a request
    should be sent through the shadow testing pipeline.
    """

    def __init__(self, config: ShadowTestConfig):
        self.config = config
        self._mirrored_count = 0
        self._total_count = 0

    def should_mirror(self, request: InferenceRequest) -> bool:
        """
        Determine if a request should be mirrored.
        
        Uses the shadow_traffic_percentage and sample_rate from config.
        Also supports per-user or per-session overrides via metadata.
        """
        self._total_count += 1

        # Check for explicit override in request metadata
        force_shadow = request.metadata.get("force_shadow", None)
        if force_shadow is not None:
            result = bool(force_shadow)
            if result:
                self._mirrored_count += 1
            return result

        # Calculate effective sample rate
        effective_rate = (
            self.config.shadow_traffic_percentage / 100.0
        ) * self.config.sample_rate

        result = random.random() < effective_rate
        if result:
            self._mirrored_count += 1
        return result

    @property
    def mirror_rate(self) -> float:
        """Actual mirror rate observed so far."""
        if self._total_count == 0:
            return 0.0
        return self._mirrored_count / self._total_count

    @property
    def stats(self) -> dict:
        """Return mirroring statistics."""
        return {
            "total_requests": self._total_count,
            "mirrored_requests": self._mirrored_count,
            "mirror_rate": self.mirror_rate,
        }
