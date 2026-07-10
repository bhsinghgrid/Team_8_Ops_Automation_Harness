"""
Response Comparator — structural and semantic comparison of model outputs.
"""

import logging
from typing import Dict, Any

from shadow_agent_framework.models.schemas import InferenceResponse

logger = logging.getLogger(__name__)


class ResponseComparator:
    """
    Compares champion and challenger responses on structural metrics.
    
    Provides:
    - Length comparison
    - Token efficiency
    - Structural similarity (heuristic-based)
    """

    def compare(
        self,
        champion: InferenceResponse,
        challenger: InferenceResponse,
    ) -> Dict[str, Any]:
        """
        Compare two model responses on structural dimensions.
        
        Returns a dict of comparison metrics.
        """
        # Convert content to string if it's a list for length comparison
        champion_content_str = str(champion.content) if isinstance(champion.content, list) else champion.content
        challenger_content_str = str(challenger.content) if isinstance(challenger.content, list) else challenger.content

        champion_len = len(champion_content_str) if champion_content_str else 0
        challenger_len = len(challenger_content_str) if challenger_content_str else 0

        # Length comparison
        length_ratio = challenger_len / champion_len if champion_len > 0 else 0.0

        # Token efficiency (output tokens per character)
        champion_tokens = champion.usage.get("completion_tokens", 0)
        challenger_tokens = challenger.usage.get("completion_tokens", 0)

        # Structural similarity (simple heuristic)
        structural_similarity = self._compute_structural_similarity(
            champion_content_str or "", challenger_content_str or ""
        )

        return {
            "champion_length": champion_len,
            "challenger_length": challenger_len,
            "length_ratio": round(length_ratio, 3),
            "champion_completion_tokens": champion_tokens,
            "challenger_completion_tokens": challenger_tokens,
            "token_efficiency_delta": challenger_tokens - champion_tokens,
            "structural_similarity": round(structural_similarity, 3),
            "both_succeeded": (
                champion.status.value == "completed"
                and challenger.status.value == "completed"
            ),
        }

    def _compute_structural_similarity(self, text_a: str, text_b: str) -> float:
        """
        Compute a simple structural similarity between two texts.
        
        Uses a combination of:
        - Paragraph count similarity
        - Average sentence length similarity
        - Common word overlap (Jaccard)
        """
        if not text_a or not text_b:
            return 0.0

        # Paragraph similarity
        paras_a = [p.strip() for p in text_a.split("\n\n") if p.strip()]
        paras_b = [p.strip() for p in text_b.split("\n\n") if p.strip()]
        para_sim = min(len(paras_a), len(paras_b)) / max(len(paras_a), len(paras_b), 1)

        # Word overlap (Jaccard)
        words_a = set(text_a.lower().split())
        words_b = set(text_b.lower().split())
        if words_a or words_b:
            jaccard = len(words_a & words_b) / len(words_a | words_b)
        else:
            jaccard = 0.0

        # Average sentence length similarity
        def avg_sentence_len(text: str) -> float:
            sentences = [s.strip() for s in text.split(".") if s.strip()]
            if not sentences:
                return 0.0
            return sum(len(s.split()) for s in sentences) / len(sentences)

        avg_a = avg_sentence_len(text_a)
        avg_b = avg_sentence_len(text_b)
        if max(avg_a, avg_b) > 0:
            sent_sim = min(avg_a, avg_b) / max(avg_a, avg_b)
        else:
            sent_sim = 0.0

        # Weighted combination
        return 0.3 * para_sim + 0.5 * jaccard + 0.2 * sent_sim
