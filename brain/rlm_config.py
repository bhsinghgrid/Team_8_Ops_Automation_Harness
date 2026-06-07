"""
Configuration and utilities for Recursive Language Model.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import json
from enum import Enum


class ModelType(Enum):
    """Types of RLM models."""
    BASIC = "basic"
    ADVANCED = "advanced"
    CUSTOM = "custom"


@dataclass
class RLMConfig:
    """Configuration for RLM."""
    # Model architecture
    model_type: ModelType = ModelType.BASIC
    d_model: int = 768
    num_layers: int = 12
    num_heads: int = 12
    d_ff: int = 3072
    vocab_size: int = 50257

    # Recursion parameters
    max_depth: int = 10
    min_context_length: int = 50
    max_context_size: int = 10000

    # Decomposition parameters
    decomposition_strategy: str = "semantic"
    min_subtask_length: int = 20

    # Composition parameters
    aggregation_strategy: str = "weighted"
    composition_confidence_threshold: float = 0.5

    # Cache parameters
    max_cache_size: int = 1000
    cache_enabled: bool = True

    # Tokenizer parameters
    tokenizer_type: str = "standard"
    vocab_min_frequency: int = 1

    # Generation parameters
    max_generation_length: int = 256
    generation_strategy: str = "beam_search"
    beam_width: int = 5
    temperature: float = 1.0
    top_k: int = 50
    top_p: float = 0.9

    # Training parameters
    learning_rate: float = 1e-4
    batch_size: int = 32
    num_epochs: int = 10
    dropout_rate: float = 0.1
    weight_decay: float = 1e-5

    # Device and precision
    device: str = "cpu"
    mixed_precision: bool = False

    # Logging and checkpointing
    log_interval: int = 100
    checkpoint_interval: int = 1000
    checkpoint_dir: str = "./checkpoints"

    # Additional metadata
    model_name: str = "rlm_base"
    version: str = "1.0.0"
    description: str = "Recursive Language Model"

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        config_dict = {}
        for key, value in self.__dict__.items():
            if isinstance(value, Enum):
                config_dict[key] = value.value
            else:
                config_dict[key] = value
        return config_dict

    def to_json(self) -> str:
        """Convert config to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @staticmethod
    def from_dict(config_dict: Dict[str, Any]) -> "RLMConfig":
        """Create config from dictionary."""
        # Convert string model_type back to enum if needed
        if isinstance(config_dict.get("model_type"), str):
            config_dict["model_type"] = ModelType(config_dict["model_type"])

        return RLMConfig(**config_dict)

    @staticmethod
    def from_json(json_str: str) -> "RLMConfig":
        """Create config from JSON string."""
        config_dict = json.loads(json_str)
        return RLMConfig.from_dict(config_dict)


class PresetConfigs:
    """Preset configurations for different RLM sizes."""

    @staticmethod
    def small() -> RLMConfig:
        """Small RLM configuration."""
        return RLMConfig(
            model_type=ModelType.BASIC,
            d_model=256,
            num_layers=6,
            num_heads=8,
            d_ff=1024,
            vocab_size=10000,
            model_name="rlm_small",
        )

    @staticmethod
    def medium() -> RLMConfig:
        """Medium RLM configuration."""
        return RLMConfig(
            model_type=ModelType.BASIC,
            d_model=512,
            num_layers=12,
            num_heads=8,
            d_ff=2048,
            vocab_size=30000,
            model_name="rlm_medium",
        )

    @staticmethod
    def large() -> RLMConfig:
        """Large RLM configuration."""
        return RLMConfig(
            model_type=ModelType.ADVANCED,
            d_model=768,
            num_layers=24,
            num_heads=12,
            d_ff=3072,
            vocab_size=50000,
            model_name="rlm_large",
        )

    @staticmethod
    def xlarge() -> RLMConfig:
        """Extra large RLM configuration."""
        return RLMConfig(
            model_type=ModelType.ADVANCED,
            d_model=1024,
            num_layers=36,
            num_heads=16,
            d_ff=4096,
            vocab_size=50000,
            model_name="rlm_xlarge",
        )


def merge_configs(base_config: RLMConfig, overrides: Dict[str, Any]) -> RLMConfig:
    """Merge config overrides into base config."""
    config_dict = base_config.to_dict()
    config_dict.update(overrides)
    return RLMConfig.from_dict(config_dict)
