"""
Core Recursive Language Model (RLM) implementation.
Handles recursive decomposition and composition of language tasks.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from abc import ABC, abstractmethod
from dataclasses import dataclass
from collections import defaultdict
import json
import sqlite3
from pathlib import Path

# Create a local SQLite database for the RLM Brain's internal memory
CACHE_DB_PATH = Path(__file__).resolve().parents[2] / "rlm_brain_memory.db"


@dataclass
class RecursionLevel:
    """Represents a single level in the recursion hierarchy."""
    level: int
    context: str
    depth: int
    parent_id: Optional[str] = None
    children_ids: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.children_ids is None:
            self.children_ids = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class RLMOutput:
    """Output structure for RLM inference."""
    result: str
    confidence: float
    recursion_depth: int
    intermediate_steps: List[str]
    metadata: Dict[str, Any]


class RecursiveDecomposer:
    """Decomposes complex tasks into recursive sub-tasks."""

    def __init__(self, max_depth: int = 10, min_context_length: int = 50):
        self.max_depth = max_depth
        self.min_context_length = min_context_length
        self.decomposition_cache: Dict[str, List[str]] = {}

    def should_decompose(self, context: str, current_depth: int) -> bool:
        """Determine if context should be further decomposed."""
        word_count = len(context.split())
        return (
            len(context) > self.min_context_length
            and current_depth < self.max_depth
            and (self._has_complexity_markers(context) or word_count >= 8)
        )

    def decompose(self, context: str, current_depth: int = 0) -> List[str]:
        """Decompose context into sub-tasks."""
        cache_key = f"{context}_{current_depth}"
        if cache_key in self.decomposition_cache:
            return self.decomposition_cache[cache_key]

        if not self.should_decompose(context, current_depth):
            return [context]

        # Decompose into logical sub-tasks
        subtasks = self._split_into_subtasks(context)
        self.decomposition_cache[cache_key] = subtasks
        return subtasks

    def _has_complexity_markers(self, context: str) -> bool:
        """Check for complexity indicators in context."""
        markers = ["and", "then", "before", "after", "while", "until", ",", ";"]
        return any(marker in context.lower() for marker in markers)

    def _split_into_subtasks(self, context: str) -> List[str]:
        """Split context into logical subtasks."""
        # Split by common delimiters
        splits = []
        current = ""

        for char in context:
            current += char
            if char in ",;":
                if current.strip():
                    splits.append(current.strip())
                current = ""

        if current.strip():
            splits.append(current.strip())

        # If no splits made, return as single item
        return splits if splits else [context]


class RecursiveComposer:
    """Composes results from recursive sub-tasks back together."""

    def __init__(self, aggregation_strategy: str = "weighted"):
        self.aggregation_strategy = aggregation_strategy
        self.composition_history: List[Dict] = []

    def compose(self, results: List[Tuple[str, float]]) -> Tuple[str, float]:
        """
        Compose multiple results into single output.

        Args:
            results: List of (result_text, confidence) tuples

        Returns:
            Tuple of (composed_result, overall_confidence)
        """
        if not results:
            return "", 0.0

        if len(results) == 1:
            return results[0]

        if self.aggregation_strategy == "weighted":
            return self._weighted_composition(results)
        elif self.aggregation_strategy == "hierarchical":
            return self._hierarchical_composition(results)
        else:
            return self._simple_composition(results)

    def _weighted_composition(self, results: List[Tuple[str, float]]) -> Tuple[str, float]:
        """Compose using weighted averaging of confidence."""
        total_confidence = sum(conf for _, conf in results)
        avg_confidence = total_confidence / len(results) if results else 0.0

        # Combine text by importance (confidence-weighted)
        combined_text = " ".join(text for text, _ in results)

        return combined_text, avg_confidence

    def _hierarchical_composition(self, results: List[Tuple[str, float]]) -> Tuple[str, float]:
        """Compose using hierarchical structure."""
        # Sort by confidence
        sorted_results = sorted(results, key=lambda x: x[1], reverse=True)

        # Use highest confidence as base
        base_text = sorted_results[0][0]
        base_conf = sorted_results[0][1]

        # Enhance with supporting results
        supporting = [text for text, conf in sorted_results[1:] if conf > 0.5]

        combined = base_text
        if supporting:
            combined += " (" + ", ".join(supporting) + ")"

        return combined, base_conf

    def _simple_composition(self, results: List[Tuple[str, float]]) -> Tuple[str, float]:
        """Simple concatenation composition."""
        combined_text = " ".join(text for text, _ in results)
        avg_confidence = sum(conf for _, conf in results) / len(results)
        return combined_text, avg_confidence

    def record_composition(self, inputs: List[str], output: str, confidence: float):
        """Record composition history for analysis."""
        self.composition_history.append(
            {"inputs": inputs, "output": output, "confidence": confidence}
        )


class RecursiveContextManager:
    """Manages recursive context and state."""

    def __init__(self, max_context_size: int = 10000):
        self.max_context_size = max_context_size
        self.context_stack: List[RecursionLevel] = []
        self.context_tree: Dict[str, RecursionLevel] = {}
        self.id_counter = 0

    def push_context(self, context: str, depth: int) -> str:
        """Push new context level onto stack."""
        context_id = f"ctx_{self.id_counter}"
        self.id_counter += 1

        parent_id = (
            self.context_stack[-1].metadata.get("id") if self.context_stack else None
        )

        level = RecursionLevel(
            level=len(self.context_stack),
            context=context,
            depth=depth,
            parent_id=parent_id,
            metadata={"id": context_id, "timestamp": None},
        )

        self.context_stack.append(level)
        self.context_tree[context_id] = level

        return context_id

    def pop_context(self) -> Optional[RecursionLevel]:
        """Pop context level from stack."""
        if self.context_stack:
            return self.context_stack.pop()
        return None

    def current_context(self) -> Optional[RecursionLevel]:
        """Get current context level."""
        if self.context_stack:
            return self.context_stack[-1]
        return None

    def get_context_depth(self) -> int:
        """Get current recursion depth."""
        return len(self.context_stack)

    def clear(self):
        """Clear context stack."""
        self.context_stack = []
        self.context_tree = {}
        self.id_counter = 0

    def export_tree(self) -> Dict:
        """Export context tree as dictionary."""
        tree = {}
        for context_id, level in self.context_tree.items():
            tree[context_id] = {
                "level": level.level,
                "context": level.context,
                "depth": level.depth,
                "parent_id": level.parent_id,
                "children_ids": level.children_ids,
                "metadata": level.metadata,
            }
        return tree


class RLMCache:
    """Persistent Local SQLite Database Cache for the RLM Brain."""

    def __init__(self, max_cache_size: int = 1000):
        self.max_cache_size = max_cache_size
        self.db_path = str(CACHE_DB_PATH)
        self.hit_count = 0
        self.miss_count = 0
        self._init_db()

    def _init_db(self):
        """Creates the cache table locally."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS rlm_cache (
                    key TEXT PRIMARY KEY,
                    result TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    access_count INTEGER DEFAULT 1,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

    def get(self, key: str) -> Optional[Tuple[str, float]]:
        """Retrieve cached result from local SQLite."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT result, confidence FROM rlm_cache WHERE key = ?', (key,))
            row = cursor.fetchone()
            
            if row:
                self.hit_count += 1
                # Update access count and timestamp for LRU/LFU eviction
                cursor.execute('''
                    UPDATE rlm_cache 
                    SET access_count = access_count + 1, last_accessed = CURRENT_TIMESTAMP 
                    WHERE key = ?
                ''', (key,))
                return (row[0], row[1])
                
        self.miss_count += 1
        return None

    def set(self, key: str, result: str, confidence: float):
        """Store result in local SQLite."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM rlm_cache')
            count = cursor.fetchone()[0]
            
            if count >= self.max_cache_size:
                self._evict_lru(cursor)

            # Insert or Update the cache entry
            cursor.execute('''
                INSERT INTO rlm_cache (key, result, confidence)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    result=excluded.result,
                    confidence=excluded.confidence,
                    access_count=access_count + 1,
                    last_accessed=CURRENT_TIMESTAMP
            ''', (key, result, confidence))

    def _evict_lru(self, cursor):
        """Evict least recently used item."""
        cursor.execute('''
            DELETE FROM rlm_cache 
            WHERE key = (
                SELECT key FROM rlm_cache 
                ORDER BY access_count ASC, last_accessed ASC LIMIT 1
            )
        ''')

    def clear(self):
        """Clear the local cache."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('DELETE FROM rlm_cache')
        self.hit_count = 0
        self.miss_count = 0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM rlm_cache')
            current_size = cursor.fetchone()[0]

        total_requests = self.hit_count + self.miss_count
        hit_rate = self.hit_count / total_requests if total_requests > 0 else 0

        return {
            "size": current_size,
            "hits": self.hit_count,
            "misses": self.miss_count,
            "hit_rate": hit_rate,
            "max_size": self.max_cache_size,
        }


class BaseRecursiveLanguageModel(ABC):
    """Abstract base class for Recursive Language Models."""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.decomposer = RecursiveDecomposer(
            max_depth=self.config.get("max_depth", 10),
            min_context_length=self.config.get("min_context_length", 50),
        )
        self.composer = RecursiveComposer(
            aggregation_strategy=self.config.get("aggregation_strategy", "weighted")
        )
        self.context_manager = RecursiveContextManager(
            max_context_size=self.config.get("max_context_size", 10000)
        )
        self.cache = RLMCache(max_cache_size=self.config.get("max_cache_size", 1000))

    @abstractmethod
    def process_single(self, context: str) -> Tuple[str, float]:
        """Process a single (non-decomposed) context."""
        pass

    def process_recursive(self, context: str, depth: int = 0) -> RLMOutput:
        """
        Process context recursively.

        Args:
            context: Input context to process
            depth: Current recursion depth

        Returns:
            RLMOutput with results and metadata
        """
        # Check cache
        cache_result = self.cache.get(context)
        if cache_result:
            result_text, confidence = cache_result
            return RLMOutput(
                result=result_text,
                confidence=confidence,
                recursion_depth=depth,
                intermediate_steps=[],
                metadata={"cache_hit": True},
            )

        # Push context
        context_id = self.context_manager.push_context(context, depth)
        intermediate_steps = []

        try:
            # Check if should decompose
            if self.decomposer.should_decompose(context, depth):
                # Decompose into subtasks
                subtasks = self.decomposer.decompose(context, depth)
                intermediate_steps.append(f"Decomposed into {len(subtasks)} subtasks")

                # Process each subtask recursively
                results = []
                for subtask in subtasks:
                    sub_output = self.process_recursive(subtask, depth + 1)
                    results.append((sub_output.result, sub_output.confidence))
                    intermediate_steps.extend(sub_output.intermediate_steps)

                # Compose results
                combined_result, combined_confidence = self.composer.compose(results)
                intermediate_steps.append(
                    f"Composed {len(results)} results with confidence {combined_confidence:.2f}"
                )
            else:
                # Process directly
                combined_result, combined_confidence = self.process_single(context)
                intermediate_steps.append("Processed at base level")

            # Cache result
            self.cache.set(context, combined_result, combined_confidence)

            return RLMOutput(
                result=combined_result,
                confidence=combined_confidence,
                recursion_depth=depth,
                intermediate_steps=intermediate_steps,
                metadata={"context_id": context_id},
            )

        finally:
            # Pop context
            self.context_manager.pop_context()

    def get_statistics(self) -> Dict[str, Any]:
        """Get RLM statistics."""
        return {
            "cache_stats": self.cache.get_stats(),
            "context_depth": self.context_manager.get_context_depth(),
            "composition_history": len(self.composer.composition_history),
        }

    def clear(self):
        """Clear all internal state."""
        self.cache.clear()
        self.context_manager.clear()
        self.composer.composition_history.clear()
