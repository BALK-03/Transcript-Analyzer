from typing import Any
from src.models.base_model import BaseAIModel

class AIModelFactory:
    _models = {}

    @classmethod
    def register_model(cls, model_type: str, model_class: type):
        """Register a new model type with the factory."""
        if not issubclass(model_class, BaseAIModel):
            raise TypeError("Registered class must be a subclass of BaseAIModel.")
        cls._models[model_type.lower()] = model_class

    @classmethod
    def create_model(cls, model_type: str, config: dict[str, Any] = None) -> BaseAIModel:
        """Create AI model instance."""
        key = model_type.strip().lower()
        model_class = cls._models.get(key)
        if not model_class:
            raise ValueError(f"Unknown model type: {model_type}. Available: {list(cls._models.keys())}")
        return model_class(config)

    @classmethod
    def get_available_models(cls) -> list:
        """Get list of available model types."""
        return list(cls._models.keys())
















# class AIModelFactory:
#     """Factory to create AI models"""

#     _models = {
#         "gemini": GeminiAIModel,
#         "openai": OpenAIAIModel,
#     }

#     @classmethod
#     def create_model(cls, model_type: str, config: dict[str, Any] = None) -> BaseAIModel:
#         """Create AI model instance"""
#         key = model_type.strip().lower()
#         if key not in cls._models:
#             raise ValueError(f"Unknown model type: {model_type}. Available: {list(cls._models.keys())}")
        
#         return cls._models[key](config)

#     @classmethod
#     def get_available_models(cls) -> list:
#         """Get list of available model types"""
#         return list(cls._models.keys())