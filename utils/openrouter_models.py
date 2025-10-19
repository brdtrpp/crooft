"""
OpenRouter Models Fetcher
Fetches and caches available models from OpenRouter API
"""

import requests
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timedelta


class OpenRouterModels:
    """Fetch and cache OpenRouter models"""

    CACHE_FILE = "openrouter_models_cache.json"
    CACHE_DURATION = timedelta(hours=24)  # Refresh cache daily
    API_URL = "https://openrouter.ai/api/v1/models"

    # Known reasoning model patterns
    REASONING_PATTERNS = [
        'o1', 'o3', 'qwq', 'deepseek-r1', 'deepseek-reasoner',
        'deepthink', 'thinking', 'reasoning', 'r1-'
    ]

    def __init__(self, cache_dir: str = "."):
        """Initialize with cache directory"""
        self.cache_path = Path(cache_dir) / self.CACHE_FILE

    def _is_reasoning_model(self, model: Dict) -> bool:
        """Determine if a model has reasoning/thinking capabilities"""
        model_id = model.get('id', '').lower()
        name = model.get('name', '').lower()
        description = model.get('description', '').lower()

        # Check patterns in ID, name, or description
        combined = f"{model_id} {name} {description}"
        return any(pattern in combined for pattern in self.REASONING_PATTERNS)

    def _fetch_from_api(self) -> List[Dict]:
        """Fetch models from OpenRouter API"""
        try:
            response = requests.get(self.API_URL, timeout=10)
            response.raise_for_status()

            models = response.json().get('data', [])

            # Process models
            model_list = []
            for model in models:
                model_id = model.get('id', '')
                if not model_id:
                    continue

                model_list.append({
                    'id': model_id,
                    'name': model.get('name', model_id),
                    'reasoning': self._is_reasoning_model(model),
                    'context_length': model.get('context_length', 0),
                    'pricing': model.get('pricing', {}),
                    'description': model.get('description', '')
                })

            # Sort alphabetically by ID
            model_list.sort(key=lambda x: x['id'])

            return model_list

        except Exception as e:
            print(f"Error fetching models from OpenRouter: {e}")
            return []

    def _load_from_cache(self) -> Optional[List[Dict]]:
        """Load models from cache if valid"""
        if not self.cache_path.exists():
            return None

        try:
            with open(self.cache_path, 'r') as f:
                cache_data = json.load(f)

            # Check cache timestamp
            cached_at = datetime.fromisoformat(cache_data.get('cached_at', '2000-01-01'))
            if datetime.now() - cached_at > self.CACHE_DURATION:
                return None  # Cache expired

            return cache_data.get('models', [])

        except Exception as e:
            print(f"Error loading cache: {e}")
            return None

    def _save_to_cache(self, models: List[Dict]):
        """Save models to cache"""
        try:
            cache_data = {
                'cached_at': datetime.now().isoformat(),
                'models': models
            }

            with open(self.cache_path, 'w') as f:
                json.dump(cache_data, f, indent=2)

        except Exception as e:
            print(f"Error saving cache: {e}")

    def get_models(self, use_cache: bool = True) -> List[Dict]:
        """
        Get list of OpenRouter models

        Args:
            use_cache: Whether to use cached data (default: True)

        Returns:
            List of model dictionaries with id, name, and reasoning flag
        """
        # Try cache first
        if use_cache:
            cached_models = self._load_from_cache()
            if cached_models:
                return cached_models

        # Fetch from API
        models = self._fetch_from_api()

        # Save to cache
        if models:
            self._save_to_cache(models)

        return models

    def get_model_choices(self, include_reasoning_indicator: bool = True) -> List[str]:
        """
        Get formatted model choices for dropdown

        Args:
            include_reasoning_indicator: Add 🧠 emoji for reasoning models

        Returns:
            List of formatted strings for display
        """
        models = self.get_models()

        choices = []
        for model in models:
            model_id = model['id']
            if include_reasoning_indicator and model['reasoning']:
                choices.append(f"🧠 {model_id}")
            else:
                choices.append(model_id)

        return choices

    def get_model_id_from_choice(self, choice: str) -> str:
        """
        Extract model ID from formatted choice string

        Args:
            choice: Formatted choice string (may include emoji)

        Returns:
            Clean model ID
        """
        # Remove reasoning indicator if present
        return choice.replace("🧠 ", "").strip()

    def get_reasoning_models(self) -> List[Dict]:
        """Get only reasoning/thinking models"""
        models = self.get_models()
        return [m for m in models if m['reasoning']]

    def get_non_reasoning_models(self) -> List[Dict]:
        """Get only non-reasoning models"""
        models = self.get_models()
        return [m for m in models if not m['reasoning']]

    def refresh_cache(self) -> int:
        """Force refresh cache from API"""
        models = self._fetch_from_api()
        if models:
            self._save_to_cache(models)
        return len(models)
