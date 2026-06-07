"""
LangGraph-based Recursive Language Model (RLM) Core
Refactored to use LangGraph for state management and orchestration
"""

from typing import Dict, List, Tuple, Optional, Any, TypedDict
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from abc import ABC, abstractmethod

from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage


class RLMState(TypedDict, total=False):
    """State for RLM processing in LangGraph"""
    input_text: str
    current_depth: int
    max_depth: int
    retry_count: int
    decomposed_tasks: List[str]
    task_results: List[Tuple[str, float]]
    final_result: str
    confidence: float
    intermediate_steps: List[str]
    cache_hits: int
    messages: List[BaseMessage]
    metadata: Dict[str, Any]


class ProcessingNode(Enum):
    """Node types in RLM graph"""
    CACHE_CHECK = "cache_check"
    COMPLEXITY_ANALYSIS = "complexity_analysis"
    DECOMPOSE = "decompose"
    PROCESS_BASE = "process_base"
    COMPOSE = "compose"
    CRITIQUE = "critique"
    CACHE_STORE = "cache_store"


@dataclass
class NodeResult:
    """Result from a node in the graph"""
    node_type: ProcessingNode
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    next_node: Optional[ProcessingNode] = None


class RLMCacheNode:
    """LangGraph Node: Cache Check"""

    def __init__(self, cache: 'RLMCache'):
        self.cache = cache

    def __call__(self, state: RLMState) -> Dict:
        """Check cache for existing result"""
        text = state.get("input_text", "")
        
        cached_result = self.cache.get(text)
        if cached_result:
            result, confidence = cached_result
            state["final_result"] = result
            state["confidence"] = confidence
            state["cache_hits"] = state.get("cache_hits", 0) + 1
            state["intermediate_steps"].append("Cache hit")
            return {
                **state,
                "cached": True,
                "should_process": False,
            }
        
        state["intermediate_steps"].append("Cache miss")
        return {
            **state,
            "cached": False,
            "should_process": True,
        }


class ComplexityAnalysisNode:
    """LangGraph Node: Analyze text complexity"""

    def __init__(self, min_length: int = 50):
        self.min_length = min_length

    def __call__(self, state: RLMState) -> Dict:
        """Analyze complexity to decide decomposition"""
        text = state.get("input_text", "")
        depth = state.get("current_depth", 0)
        max_depth = state.get("max_depth", 10)

        # Check complexity markers
        complexity_markers = ["and", "then", "before", "after", "while", ",", ";"]
        has_markers = any(marker in text.lower() for marker in complexity_markers)

        should_decompose = (
            len(text) > self.min_length
            and depth < max_depth
            and has_markers
        )

        state["intermediate_steps"].append(
            f"Complexity analysis: decompose={should_decompose}"
        )

        return {
            **state,
            "should_decompose": should_decompose,
            "complexity_score": float(len(text)) / max(self.min_length, 1),
        }


class DecompositionNode:
    """LangGraph Node: Decompose text into subtasks"""

    def __call__(self, state: RLMState) -> Dict:
        """Decompose text into subtasks"""
        text = state.get("input_text", "")
        
        # Simple decomposition by common delimiters
        subtasks = []
        current = ""

        for char in text:
            current += char
            if char in ",;":
                if current.strip():
                    subtasks.append(current.strip())
                current = ""

        if current.strip():
            subtasks.append(current.strip())

        # If no splits, return as single task
        if not subtasks:
            subtasks = [text]

        state["intermediate_steps"].append(
            f"Decomposed into {len(subtasks)} subtasks"
        )

        return {
            **state,
            "decomposed_tasks": subtasks,
            "num_subtasks": len(subtasks),
        }


class BaseProcessingNode(ABC):
    """Base class for text processing nodes"""

    @abstractmethod
    def process(self, text: str) -> Tuple[str, float]:
        """Process text and return result with confidence"""
        pass

    def __call__(self, state: RLMState) -> Dict:
        """Process current input"""
        text = state.get("input_text", "")
        tasks = list(state.get("decomposed_tasks") or [])
        if not tasks and text:
            tasks = [text]

        if not tasks:
            return {
                **state,
                "task_result": ("", 0.0),
                "task_results": list(state.get("task_results", [])),
            }

        task_results = list(state.get("task_results", []))
        for task in tasks:
            result, confidence = self.process(task)
            task_results.append((result, confidence))

        result, confidence = task_results[-1] if task_results else ("", 0.0)
        
        return {
            **state,
            "task_result": (result, confidence),
            "task_results": task_results,
        }


class CompositionNode:
    """LangGraph Node: Compose results from subtasks"""

    def __init__(self, aggregation_strategy: str = "weighted"):
        self.aggregation_strategy = aggregation_strategy

    def __call__(self, state: RLMState) -> Dict:
        """Compose results from multiple subtasks"""
        results = state.get("task_results", [])
        if not results and state.get("task_result"):
            results = [state["task_result"]]
        
        if not results:
            final_result = ""
            confidence = 0.0
        elif len(results) == 1:
            final_result, confidence = results[0]
        else:
            if self.aggregation_strategy == "weighted":
                final_result, confidence = self._weighted_composition(results)
            else:
                final_result, confidence = self._simple_composition(results)

        state["intermediate_steps"].append(
            f"Composed {len(results)} results with confidence {confidence:.2f}"
        )

        return {
            **state,
            "final_result": final_result,
            "confidence": confidence,
        }

    @staticmethod
    def _weighted_composition(results: List[Tuple[str, float]]) -> Tuple[str, float]:
        """Compose using weighted averaging"""
        total_confidence = sum(conf for _, conf in results)
        avg_confidence = total_confidence / len(results) if results else 0.0
        combined_text = " ".join(text for text, _ in results)
        return combined_text, avg_confidence

    @staticmethod
    def _simple_composition(results: List[Tuple[str, float]]) -> Tuple[str, float]:
        """Simple concatenation composition"""
        combined_text = " ".join(text for text, _ in results)
        avg_confidence = sum(conf for _, conf in results) / len(results)
        return combined_text, avg_confidence


class CacheStoreNode:
    """LangGraph Node: Store result in cache"""

    def __init__(self, cache: 'RLMCache'):
        self.cache = cache

    def __call__(self, state: RLMState) -> Dict:
        """Store result in cache"""
        text = state.get("input_text", "")
        result = state.get("final_result", "")
        confidence = state.get("confidence", 0.0)

        if text and result:
            self.cache.set(text, result, confidence)
            if "intermediate_steps" in state:
                state["intermediate_steps"].append("Result cached")

        return dict(state)

class SelfCritiqueNode:
    """LangGraph Node: Self-Critique"""

    def __call__(self, state: RLMState) -> Dict:
        """Critique the composed result."""
        final_result = state.get("final_result", "")
        confidence = state.get("confidence", 0.0)
        retry_count = state.get("retry_count", 0)
        
        # Simple simulated critique based on confidence.
        # In a real implementation, you could call self.processing_node or an LLM here.
        needs_revision = False
        
        if confidence < 0.3 and retry_count < 2:
            needs_revision = True
            
        if "intermediate_steps" in state:
            if needs_revision:
                state["intermediate_steps"].append(f"Critique failed (confidence {confidence:.2f}). Revising...")
            else:
                state["intermediate_steps"].append("Critique passed.")

        return {
            **state,
            "needs_revision": needs_revision,
            "retry_count": retry_count + 1 if needs_revision else retry_count
        }

# Import the real SQLite database cache from rlm_core instead of using an in-memory dictionary
from .rlm_core import RLMCache

class RLMGraph:
    """LangGraph-based RLM orchestration"""

    def __init__(
        self,
        processing_node: BaseProcessingNode,
        max_depth: int = 10,
        min_complexity: int = 50,
    ):
        self.processing_node = processing_node
        self.max_depth = max_depth
        self.min_complexity = min_complexity
        self.cache = RLMCache()

        # Initialize LangGraph
        self.graph = self._build_graph()

    def _build_graph(self) -> Any:
        """Build the RLM processing graph"""
        graph = StateGraph(RLMState)

        # Create nodes
        cache_node = RLMCacheNode(self.cache)
        complexity_node = ComplexityAnalysisNode(min_length=self.min_complexity)
        decompose_node = DecompositionNode()
        composition_node = CompositionNode()
        critique_node = SelfCritiqueNode()
        cache_store_node = CacheStoreNode(self.cache)

        # Add nodes to graph
        graph.add_node("cache_check", cache_node)
        graph.add_node("complexity_analysis", complexity_node)
        graph.add_node("decompose", decompose_node)
        graph.add_node("process_base", self.processing_node)
        graph.add_node("compose", composition_node)
        graph.add_node("critique", critique_node)
        graph.add_node("cache_store", cache_store_node)

        # Set entry point
        graph.set_entry_point("cache_check")

        # Add conditional edges
        graph.add_conditional_edges(
            "cache_check",
            self._route_after_cache,
            {
                "continue": "complexity_analysis",
                "end": END,
            },
        )

        # Complexity analysis -> decompose or process
        graph.add_conditional_edges(
            "complexity_analysis",
            self._route_after_complexity,
            {
                "decompose": "decompose",
                "process": "process_base",
            },
        )

        # Decompose -> process (multiple times via recursive handling)
        graph.add_edge("decompose", "process_base")

        # Process -> composition
        graph.add_edge("process_base", "compose")

        # Compose -> Critique
        graph.add_edge("compose", "critique")

        # Critique conditional routing
        graph.add_conditional_edges(
            "critique",
            self._route_after_critique,
            {
                "pass": "cache_store",
                "retry": "process_base"
            }
        )

        # Cache store -> end
        graph.add_edge("cache_store", END)

        return graph.compile()

    def _route_after_critique(self, state: RLMState) -> str:
        """Route based on self-critique output."""
        return "retry" if state.get("needs_revision", False) else "pass"

    def _route_after_complexity(self, state: RLMState) -> str:
        """Route based on complexity analysis"""
        text = state.get("input_text", "")
        depth = state.get("current_depth", 0)
        max_depth = state.get("max_depth", self.max_depth)
        has_markers = any(marker in text.lower() for marker in ["and", "then", "before", "after", "while", ",", ";"])
        word_count = len(text.split())
        should_decompose = (
            len(text) > self.min_complexity
            and depth < max_depth
            and (has_markers or word_count >= 8)
        )

        if should_decompose:
            return "decompose"
        else:
            return "process"

    @staticmethod
    def _route_after_cache(state: RLMState) -> str:
        """Route around the rest of the graph when a cached result exists."""
        return "end" if state.get("cached", False) else "continue"

    def process(self, text: str) -> RLMState:
        """Process text through the graph"""
        initial_state: RLMState = {
            "input_text": text,
            "current_depth": 0,
            "max_depth": self.max_depth,
            "decomposed_tasks": [],
            "task_results": [],
            "final_result": "",
            "confidence": 0.0,
            "intermediate_steps": [],
            "cache_hits": 0,
            "messages": [HumanMessage(content=text)],
            "metadata": {},
        }

        return self.graph.invoke(initial_state)

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return self.cache.get_stats()
