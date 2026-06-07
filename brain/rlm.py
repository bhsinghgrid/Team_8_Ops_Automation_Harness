"""
Main RLM model implementation.
Integrates all RLM components.
"""

from typing import Optional, Dict, Any, Tuple
from .rlm_core import BaseRecursiveLanguageModel, RLMOutput
from .tokenizer import Tokenizer, Vocabulary, TokenizerFactory
from .rlm_config import RLMConfig, PresetConfigs
from .attention import MultiHeadAttention, RecursiveAttention
import numpy as np


class RecursiveLanguageModel(BaseRecursiveLanguageModel):
    """
    Concrete implementation of Recursive Language Model.
    
    Integrates recursive decomposition, composition, attention,
    and caching for efficient language understanding and generation.
    """

    def __init__(
        self,
        config: Optional[RLMConfig] = None,
        tokenizer: Optional[Tokenizer] = None,
    ):
        """
        Initialize RLM.

        Args:
            config: RLM configuration
            tokenizer: Tokenizer instance
        """
        if config is None:
            config = PresetConfigs.medium()

        self.config = config
        
        # Initialize tokenizer
        if tokenizer is None:
            vocabulary = Vocabulary(min_frequency=config.vocab_min_frequency)
            self.tokenizer = TokenizerFactory.create_tokenizer(
                tokenizer_type=config.tokenizer_type,
                vocabulary=vocabulary,
            )
        else:
            self.tokenizer = tokenizer

        # Convert config to base config dict
        config_dict = config.to_dict()
        
        # Initialize base class
        super().__init__(config=config_dict)
        # Keep the public config as the dataclass expected by the API/tests.
        self.config = config

        # Initialize attention mechanisms
        self.multi_head_attention = MultiHeadAttention(
            d_model=config.d_model,
            num_heads=config.num_heads,
            dropout_rate=config.dropout_rate,
        )
        self.recursive_attention = RecursiveAttention(
            d_model=config.d_model,
            depth_weight=0.5,
        )

        # Initialize embeddings (placeholder)
        self.embeddings = np.random.randn(config.vocab_size, config.d_model) * 0.02

        # Model state
        self.is_trained = False
        self.training_stats: Dict[str, Any] = {}

    def process_single(self, context: str) -> Tuple[str, float]:
        """
        Process single context at base level.

        Args:
            context: Input context

        Returns:
            Tuple of (result, confidence)
        """
        # Tokenize
        tokens = self.tokenizer.tokenize(context)
        
        if not tokens:
            return "", 0.0

        # Encode tokens
        token_ids = self.tokenizer.encode(context)
        
        if not token_ids:
            return "", 0.0

        # Simple scoring based on token embedding similarity
        embeddings = self.embeddings[token_ids]
        
        # Compute mean embedding
        mean_embedding = embeddings.mean(axis=0)
        
        # Compute confidence from norm
        confidence = min(1.0, float(np.linalg.norm(mean_embedding) / 100.0))

        # Generate result (simplified)
        result = f"Processed: {context[:50]}..." if len(context) > 50 else f"Processed: {context}"

        return result, confidence

    def encode(self, text: str) -> np.ndarray:
        """Encode text to embeddings."""
        token_ids = self.tokenizer.encode(text)
        embeddings = self.embeddings[token_ids]
        return embeddings.mean(axis=0)

    def decode_embeddings(self, embeddings: np.ndarray) -> str:
        """Decode embeddings back to text (approximate)."""
        # Find nearest token embeddings
        distances = np.linalg.norm(self.embeddings - embeddings, axis=1)
        nearest_token_id = np.argmin(distances)
        
        # Decode
        return self.tokenizer.decode([nearest_token_id])

    def train_mode(self):
        """Set model to training mode."""
        # In a real implementation, would set dropout, etc.
        pass

    def eval_mode(self):
        """Set model to evaluation mode."""
        # In a real implementation, would disable dropout, etc.
        pass

    def forward(self, input_ids: np.ndarray) -> np.ndarray:
        """
        Forward pass through model.

        Args:
            input_ids: Token IDs array

        Returns:
            Output logits
        """
        # Get embeddings
        embeddings = self.embeddings[input_ids]

        # Apply attention (simplified)
        query = embeddings
        key = embeddings
        value = embeddings

        attention_output = self.multi_head_attention.compute(query, key, value)

        # Simple projection to vocabulary
        batch_size = input_ids.shape[0]
        seq_len = input_ids.shape[1]
        
        # Project to vocabulary logits
        logits = np.dot(attention_output, self.embeddings.T)

        return logits

    def save_config(self, path: str):
        """Save configuration to file."""
        json_config = self.config.to_json()
        with open(path, 'w') as f:
            f.write(json_config)

    def load_config(self, path: str):
        """Load configuration from file."""
        with open(path, 'r') as f:
            json_config = f.read()
        self.config = RLMConfig.from_json(json_config)

    def get_config(self) -> RLMConfig:
        """Get current configuration."""
        return self.config

    def set_config(self, config: RLMConfig):
        """Set configuration."""
        self.config = config

    def __repr__(self):
        return (
            f"RecursiveLanguageModel(\n"
            f"  model_name={self.config.model_name},\n"
            f"  d_model={self.config.d_model},\n"
            f"  num_layers={self.config.num_layers},\n"
            f"  num_heads={self.config.num_heads},\n"
            f"  max_depth={self.config.max_depth},\n"
            f")"
        )


class RLMBuilder:
    """Builder for creating RLM instances."""

    def __init__(self):
        self.config = PresetConfigs.medium()
        self.tokenizer: Optional[Tokenizer] = None

    def with_config(self, config: RLMConfig) -> "RLMBuilder":
        """Set configuration."""
        self.config = config
        return self

    def with_preset(self, preset: str) -> "RLMBuilder":
        """Use preset configuration."""
        if preset == "small":
            self.config = PresetConfigs.small()
        elif preset == "medium":
            self.config = PresetConfigs.medium()
        elif preset == "large":
            self.config = PresetConfigs.large()
        elif preset == "xlarge":
            self.config = PresetConfigs.xlarge()
        else:
            raise ValueError(f"Unknown preset: {preset}")
        return self

    def with_tokenizer(self, tokenizer: Tokenizer) -> "RLMBuilder":
        """Set tokenizer."""
        self.tokenizer = tokenizer
        return self

    def with_vocab_size(self, vocab_size: int) -> "RLMBuilder":
        """Set vocabulary size."""
        self.config.vocab_size = vocab_size
        return self

    def with_max_depth(self, max_depth: int) -> "RLMBuilder":
        """Set maximum recursion depth."""
        self.config.max_depth = max_depth
        return self

    def build(self) -> RecursiveLanguageModel:
        """Build and return RLM instance."""
        return RecursiveLanguageModel(config=self.config, tokenizer=self.tokenizer)
