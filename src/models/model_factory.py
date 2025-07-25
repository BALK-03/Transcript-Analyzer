import os, sys
from typing import Any

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.models.base_model import BaseAIModel
from src.models.gemini_model import GeminiAIModel
from src.models.openai_model import OpenAIAIModel

class AIModelFactory:
    """Factory to create AI models"""

    _models = {
        "gemini": GeminiAIModel,
        "openai": OpenAIAIModel,
    }

    @classmethod
    def create_model(cls, model_type: str, config: dict[str, Any] = None) -> BaseAIModel:
        """Create AI model instance"""
        key = model_type.strip().lower()
        if key not in cls._models:
            raise ValueError(f"Unknown model type: {model_type}. Available: {list(cls._models.keys())}")
        
        return cls._models[key](config)

    @classmethod
    def get_available_models(cls) -> list:
        """Get list of available model types"""
        return list(cls._models.keys())