"""
Shadow Test Storage — in-memory storage for shadow test results.
"""

import logging
import json
import dataclasses
from typing import Dict, List, Any, Optional

import redis.asyncio as redis
from redis.asyncio.client import Redis

from shadow_agent_framework.config.settings import RedisConfig
from shadow_agent_framework.models.schemas import EvaluationResult, GatingResult, PromotionStatus, HumanReviewItem

logger = logging.getLogger(__name__)


class ShadowTestStorage:
    """
    Stores shadow test evaluation results and gating events in Redis.
    """

    def __init__(self, config: RedisConfig):
        self._config = config
        self._redis: Optional[Redis] = None

    async def initialize(self) -> None:
        """Initialize the storage backend."""
        try:
            self._redis = redis.from_url(
                f"redis://{self._config.host}:{self._config.port}",
                db=self._config.db,
                password=self._config.password,
                decode_responses=True
            )
            await self._redis.ping()
            logger.info(f"ShadowTestStorage initialized (Redis @ {self._config.host}:{self._config.port})")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}", exc_info=True)
            self._redis = None

    async def close(self) -> None:
        """Close the storage backend."""
        if self._redis:
            await self._redis.close()
            logger.info("ShadowTestStorage closed (Redis connection)")

    async def store_evaluation(self, result: EvaluationResult) -> None:
        """Store an evaluation result."""
        if not self._redis:
            logger.warning("Storage not initialized — skipping store_evaluation")
            return
        key = f"evaluation:{result.request_id}"
        await self._redis.set(key, json.dumps(dataclasses.asdict(result)))

    async def store_gating_event(
        self, event: GatingResult, promotion_status: PromotionStatus = PromotionStatus.HOLD
    ) -> None:
        """Store a gating event."""
        if not self._redis:
            logger.warning("Storage not initialized — skipping store_gating_event")
            return
        key = f"gating_event:{event.timestamp}"
        await self._redis.set(key, json.dumps({
            "event": dataclasses.asdict(event),
            "promotion_status": promotion_status.value,
        }))

    async def get_all_evaluations(self, test_name: str = "") -> List[EvaluationResult]:
        """Retrieve all stored evaluations."""
        if not self._redis:
            return []
        keys = await self._redis.keys("evaluation:*")
        if not keys:
            return []
        
        evaluations = []
        for key in keys:
            data = await self._redis.get(key)
            # This is a simplification; a production system would need robust deserialization
            # with error handling and schema evolution considerations.
            evaluations.append(EvaluationResult(**json.loads(data)))
        return evaluations

    async def get_evaluation(self, request_id: str) -> Optional[EvaluationResult]:
        """Retrieve a specific evaluation by request ID."""
        if not self._redis:
            return None
        key = f"evaluation:{request_id}"
        data = await self._redis.get(key)
        return EvaluationResult(**json.loads(data)) if data else None

    async def get_evaluation_count(self) -> int:
        """Return the number of stored evaluations."""
        if not self._redis:
            return 0
        return len(await self._redis.keys("evaluation:*"))

    async def store_human_review_item(self, item: HumanReviewItem) -> None:
        """
        Store a human review item.
        """
        if not self._redis:
            logger.warning("Storage not initialized — skipping store_human_review_item")
            return
        key = f"human_review:{item.review_id}"
        await self._redis.set(key, json.dumps(dataclasses.asdict(item)))

    async def get_all_human_review_items(self) -> List[HumanReviewItem]:
        """
        Retrieve all stored human review items.
        """
        if not self._redis:
            return []
        keys = await self._redis.keys("human_review:*")
        if not keys:
            return []
        
        items = []
        for key in keys:
            data = await self._redis.get(key)
            items.append(HumanReviewItem(**json.loads(data)))
        return items

    async def clear(self) -> None:
        """Clear all stored data."""
        if self._redis:
            await self._redis.flushdb()
            logger.info("Cleared all data from Redis DB.")
