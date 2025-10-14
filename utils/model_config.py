"""
Model Configuration for Fiction Pipeline
"""

from typing import Dict, Optional
from pydantic import BaseModel


class AgentModelConfig(BaseModel):
    """Configuration for a single agent's model"""
    model: str = "anthropic/claude-3.5-sonnet"
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None


class ModelConfig:
    """Manages model configurations for all agents"""

    # Default configurations optimized for each stage
    DEFAULTS = {
        "series": AgentModelConfig(
            model="anthropic/claude-3.5-sonnet",
            temperature=0.3,  # Low for structured planning
            max_tokens=4000
        ),
        "book": AgentModelConfig(
            model="anthropic/claude-3.5-sonnet",
            temperature=0.3,  # Low for logical structure
            max_tokens=16000  # Higher for complete book outlines (15-20 chapters)
        ),
        "chapter": AgentModelConfig(
            model="anthropic/claude-3.5-sonnet",
            temperature=0.4,  # Slightly higher for scene creativity
            max_tokens=3000
        ),
        "scene": AgentModelConfig(
            model="anthropic/claude-3.5-sonnet",
            temperature=0.5,  # Moderate for beat planning
            max_tokens=2000
        ),
        "beat": AgentModelConfig(
            model="anthropic/claude-3.5-sonnet",
            temperature=0.3,  # Low (placeholder agent)
            max_tokens=1000
        ),
        "prose": AgentModelConfig(
            model="anthropic/claude-3.5-sonnet",
            temperature=0.8,  # HIGH for creative prose ✨
            max_tokens=2000
        ),
        "qa": AgentModelConfig(
            model="anthropic/claude-3.5-sonnet",
            temperature=0.5,  # Balanced for analysis
            max_tokens=2000
        ),
        "lore": AgentModelConfig(
            model="anthropic/claude-3.5-sonnet",
            temperature=0.4,  # Moderate for consistency checking
            max_tokens=2000
        )
    }

    @classmethod
    def create(cls, custom_config: Optional[Dict[str, Dict]] = None) -> Dict[str, AgentModelConfig]:
        """
        Create model configurations with optional overrides

        Args:
            custom_config: Dictionary of agent -> config overrides
                Example: {
                    "prose": {"model": "anthropic/claude-3-opus", "temperature": 0.9},
                    "qa": {"model": "openai/gpt-4", "temperature": 0.5}
                }

        Returns:
            Dictionary of agent -> AgentModelConfig
        """
        config = cls.DEFAULTS.copy()

        if custom_config:
            for agent, overrides in custom_config.items():
                if agent in config:
                    # Merge with defaults
                    current = config[agent].model_dump()
                    current.update(overrides)
                    config[agent] = AgentModelConfig(**current)
                else:
                    # New agent config
                    config[agent] = AgentModelConfig(**overrides)

        return config

    @classmethod
    def get_presets(cls) -> Dict[str, Dict[str, Dict]]:
        """Get preset configurations for common scenarios"""
        return {
            "balanced": {
                # Default balanced configuration
                "prose": {"temperature": 0.8}
            },
            "creative": {
                # Maximum creativity
                "series": {"temperature": 0.5},
                "book": {"temperature": 0.5},
                "chapter": {"temperature": 0.6},
                "scene": {"temperature": 0.7},
                "prose": {"temperature": 0.95},
                "qa": {"temperature": 0.6}
            },
            "precise": {
                # Maximum consistency/precision
                "series": {"temperature": 0.2},
                "book": {"temperature": 0.2},
                "chapter": {"temperature": 0.3},
                "scene": {"temperature": 0.3},
                "prose": {"temperature": 0.5},
                "qa": {"temperature": 0.3},
                "lore": {"temperature": 0.2}
            },
            "cost_optimized": {
                # Use cheaper models where possible
                "series": {"model": "anthropic/claude-3-haiku"},
                "book": {"model": "anthropic/claude-3-haiku"},
                "chapter": {"model": "anthropic/claude-3-haiku"},
                "scene": {"model": "anthropic/claude-3-haiku"},
                "beat": {"model": "anthropic/claude-3-haiku"},
                "prose": {"model": "anthropic/claude-3.5-sonnet", "temperature": 0.8},  # Keep good for prose
                "qa": {"model": "anthropic/claude-3-haiku"},
                "lore": {"model": "anthropic/claude-3-haiku"}
            },
            "premium": {
                # Best models for everything
                "series": {"model": "google/gemini-2.5-flash-lite"},
                "book": {"model": "google/gemini-2.5-flash-lite"},
                "chapter": {"model": "google/gemini-2.5-flash-lite"},
                "scene": {"model": "google/gemini-2.5-flash-lite"},
                "beat": {"model": "google/gemini-2.5-flash-lite"},
                "prose": {"model": "google/gemini-2.5-flash-lite", "temperature": 0.9},
                "qa": {"model": "google/gemini-2.5-flash-lite"},
                "lore": {"model": "google/gemini-2.5-flash-lite"}
            },
            # NSFW Presets - Use uncensored models for mature content
            # Popular NSFW models on OpenRouter (verify availability):
            # - "sao10k/l3-euryale-70b" (older, more stable)
            # - "sao10k/l3.1-euryale-70b" (newer version)
            # - "sao10k/l3-lunaris-8b" (smaller, faster)
            # - "lizpreciatior/lzlv-70b-fp16-hf" (alternative)
            # - "nousresearch/hermes-3-llama-3.1-405b" (very large, uncensored)
            "balanced_nsfw": {
                # Balanced with NSFW-capable prose model
                "prose": {
                    "model": "sao10k/l3.1-euryale-70b",  # Updated to stable version
                    "temperature": 0.85
                }
            },
            "creative_nsfw": {
                # Maximum creativity with NSFW model
                "series": {"temperature": 0.5},
                "book": {"temperature": 0.5},
                "chapter": {"temperature": 0.6},
                "scene": {"temperature": 0.7},
                "prose": {
                    "model": "sao10k/l3.1-euryale-70b",
                    "temperature": 0.95
                },
                "qa": {"temperature": 0.6}
            },
            "precise_nsfw": {
                # Precise with NSFW prose
                "series": {"temperature": 0.2},
                "book": {"temperature": 0.2},
                "chapter": {"temperature": 0.3},
                "scene": {"temperature": 0.3},
                "prose": {
                    "model": "sao10k/l3.1-euryale-70b",
                    "temperature": 0.7
                },
                "qa": {"temperature": 0.3},
                "lore": {"temperature": 0.2}
            },
            "cost_optimized_nsfw": {
                # Cheap structure models, NSFW prose only
                "series": {"model": "anthropic/claude-3-haiku"},
                "book": {"model": "anthropic/claude-3-haiku"},
                "chapter": {"model": "anthropic/claude-3-haiku"},
                "scene": {"model": "anthropic/claude-3-haiku"},
                "beat": {"model": "anthropic/claude-3-haiku"},
                "prose": {
                    "model": "sao10k/l3-lunaris-8b",  # Smaller, cheaper NSFW model
                    "temperature": 0.85
                },
                "qa": {"model": "anthropic/claude-3-haiku"},
                "lore": {"model": "anthropic/claude-3-haiku"}
            },
            "premium_nsfw": {
                # Premium models + NSFW prose
                # Note: Use full Gemini or Claude for series (not lite) to handle large book counts
                "series": {"model": "google/gemini-2.0-flash-exp:free", "max_tokens": 8000},
                "book": {"model": "google/gemini-2.5-flash-lite"},
                "chapter": {"model": "google/gemini-2.5-flash-lite"},
                "scene": {"model": "google/gemini-2.5-flash-lite"},
                "beat": {"model": "google/gemini-2.5-flash-lite"},
                "prose": {
                    "model": "nousresearch/hermes-3-llama-3.1-405b",  # Premium uncensored model
                    "temperature": 0.9
                },
                "qa": {"model": "google/gemini-2.5-flash-lite"},
                "lore": {"model": "google/gemini-2.5-flash-lite"}
            }
        }
