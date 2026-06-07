"""
Attention mechanisms for Recursive Language Model.
Implements various attention patterns for recursive processing.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from abc import ABC, abstractmethod
import math


class AttentionScore:
    """Represents attention score between tokens."""

    def __init__(self, query_idx: int, key_idx: int, score: float):
        self.query_idx = query_idx
        self.key_idx = key_idx
        self.score = score

    def __repr__(self):
        return f"AttentionScore({self.query_idx}, {self.key_idx}, {self.score:.4f})"


class BaseAttention(ABC):
    """Abstract base class for attention mechanisms."""

    @abstractmethod
    def compute(
        self, query: np.ndarray, key: np.ndarray, value: np.ndarray
    ) -> np.ndarray:
        """Compute attention output."""
        pass

    @abstractmethod
    def get_weights(
        self, query: np.ndarray, key: np.ndarray
    ) -> np.ndarray:
        """Get attention weights."""
        pass


class ScaledDotProductAttention(BaseAttention):
    """Scaled dot-product attention mechanism."""

    def __init__(self, d_k: int, dropout_rate: float = 0.1):
        self.d_k = d_k
        self.dropout_rate = dropout_rate
        self.scale = math.sqrt(d_k)

    def get_weights(
        self, query: np.ndarray, key: np.ndarray, mask: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """Compute attention weights."""
        # Compute scores
        scores = np.matmul(query, key.T) / self.scale

        # Apply mask if provided
        if mask is not None:
            scores = np.where(mask, scores, -1e9)

        # Softmax
        weights = self._softmax(scores)
        return weights

    def compute(
        self,
        query: np.ndarray,
        key: np.ndarray,
        value: np.ndarray,
        mask: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """Compute attention output."""
        weights = self.get_weights(query, key, mask)
        output = np.matmul(weights, value)
        return output

    @staticmethod
    def _softmax(x: np.ndarray) -> np.ndarray:
        """Compute softmax."""
        e_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
        return e_x / np.sum(e_x, axis=-1, keepdims=True)


class MultiHeadAttention(BaseAttention):
    """Multi-head attention mechanism."""

    def __init__(self, d_model: int, num_heads: int, dropout_rate: float = 0.1):
        assert d_model % num_heads == 0, "d_model must be divisible by num_heads"

        self.d_model = d_model
        self.num_heads = num_heads
        self.d_k = d_model // num_heads
        self.dropout_rate = dropout_rate

        self.attention_heads = [
            ScaledDotProductAttention(self.d_k, dropout_rate)
            for _ in range(num_heads)
        ]

    def get_weights(self, query: np.ndarray, key: np.ndarray) -> List[np.ndarray]:
        """Get attention weights from all heads."""
        weights = []
        for i in range(self.num_heads):
            head_weights = self.attention_heads[i].get_weights(query, key)
            weights.append(head_weights)
        return weights

    def compute(
        self,
        query: np.ndarray,
        key: np.ndarray,
        value: np.ndarray,
        mask: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """Compute multi-head attention output."""
        # Split query, key, value into multiple heads
        batch_size, seq_len, d_model = query.shape

        # Reshape for multi-head
        query_heads = self._split_heads(query)
        key_heads = self._split_heads(key)
        value_heads = self._split_heads(value)

        # Apply attention for each head
        outputs = []
        for i in range(self.num_heads):
            head_output = self.attention_heads[i].compute(
                query_heads[i], key_heads[i], value_heads[i], mask
            )
            outputs.append(head_output)

        # Concatenate heads
        concatenated = np.concatenate(outputs, axis=-1)
        return concatenated

    def _split_heads(self, x: np.ndarray) -> List[np.ndarray]:
        """Split into multiple heads."""
        batch_size, seq_len, d_model = x.shape
        heads = []

        for i in range(self.num_heads):
            start_idx = i * self.d_k
            end_idx = (i + 1) * self.d_k
            head = x[:, :, start_idx:end_idx]
            heads.append(head)

        return heads


class RecursiveAttention(BaseAttention):
    """Attention mechanism for recursive contexts."""

    def __init__(self, d_model: int, depth_weight: float = 0.5):
        self.d_model = d_model
        self.depth_weight = depth_weight
        self.base_attention = ScaledDotProductAttention(d_model)
        self.depth_scores: Dict[Tuple[int, int], float] = {}

    def compute_depth_bias(self, current_depth: int, target_depth: int) -> float:
        """Compute bias based on recursion depth."""
        depth_diff = abs(current_depth - target_depth)
        return math.exp(-depth_diff * self.depth_weight)

    def compute(
        self,
        query: np.ndarray,
        key: np.ndarray,
        value: np.ndarray,
        depths: Optional[List[int]] = None,
    ) -> np.ndarray:
        """Compute attention with depth consideration."""
        # Base attention
        output = self.base_attention.compute(query, key, value)

        # Apply depth bias if provided
        if depths is not None and len(depths) == key.shape[1]:
            depth_bias = self._compute_depth_bias_matrix(depths)
            output = output * (1 + depth_bias)

        return output

    def _compute_depth_bias_matrix(self, depths: List[int]) -> np.ndarray:
        """Compute depth bias matrix."""
        n = len(depths)
        bias_matrix = np.zeros((n, n))

        for i in range(n):
            for j in range(n):
                bias_matrix[i, j] = self.compute_depth_bias(depths[i], depths[j])

        return bias_matrix

    def get_weights(self, query: np.ndarray, key: np.ndarray) -> np.ndarray:
        """Get attention weights."""
        return self.base_attention.get_weights(query, key)


class AttentionMatrix:
    """Matrix representation of attention patterns."""

    def __init__(self, num_tokens: int):
        self.num_tokens = num_tokens
        self.matrix = np.zeros((num_tokens, num_tokens))
        self.attention_scores: List[AttentionScore] = []

    def add_score(self, query_idx: int, key_idx: int, score: float):
        """Add attention score."""
        if 0 <= query_idx < self.num_tokens and 0 <= key_idx < self.num_tokens:
            self.matrix[query_idx, key_idx] = score
            self.attention_scores.append(AttentionScore(query_idx, key_idx, score))

    def normalize(self):
        """Normalize matrix (softmax over each row)."""
        row_sums = self.matrix.sum(axis=1, keepdims=True)
        self.matrix = np.divide(
            self.matrix, row_sums, where=row_sums != 0, out=np.zeros_like(self.matrix)
        )

    def get_top_k(self, k: int) -> List[AttentionScore]:
        """Get top-k attention scores."""
        sorted_scores = sorted(
            self.attention_scores, key=lambda s: s.score, reverse=True
        )
        return sorted_scores[:k]

    def visualize(self) -> str:
        """Create text visualization of attention matrix."""
        lines = []
        lines.append("Attention Matrix:")
        lines.append("=" * (self.num_tokens * 8 + 4))

        # Header
        header = "    " + "".join(f"{i:7d}" for i in range(self.num_tokens))
        lines.append(header)

        # Rows
        for i in range(self.num_tokens):
            row = f"{i:3d} " + "".join(f"{self.matrix[i, j]:7.3f}" for j in range(self.num_tokens))
            lines.append(row)

        return "\n".join(lines)


class AttentionHead:
    """Single attention head for analysis."""

    def __init__(self, head_id: int, d_k: int):
        self.head_id = head_id
        self.d_k = d_k
        self.attention_matrix = None
        self.weights = None

    def set_weights(self, weights: np.ndarray):
        """Set attention weights."""
        self.weights = weights
        self.attention_matrix = AttentionMatrix(weights.shape[0])

        for i in range(weights.shape[0]):
            for j in range(weights.shape[1]):
                self.attention_matrix.add_score(i, j, weights[i, j])

    def __repr__(self):
        return f"AttentionHead({self.head_id}, d_k={self.d_k})"
