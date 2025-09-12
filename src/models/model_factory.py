from typing import Any
from src.models.base_model import BaseAIModel
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AIModelFactory:
    _models = {}

    @classmethod
    def register_model(cls, model_type: str, model_class: type):
        """Register a new model type with the factory."""
        logger.debug(f"Attempting to register model type: {model_type}")
        logger.debug(f"Model class: {model_class.__name__}")
        
        if not issubclass(model_class, BaseAIModel):
            logger.error(f"Registration failed: {model_class.__name__} is not a subclass of BaseAIModel")
            raise TypeError("Registered class must be a subclass of BaseAIModel.")
        
        key = model_type.lower()
        logger.debug(f"Registering model with key: {key}")
        cls._models[key] = model_class
        logger.info(f"Successfully registered model type '{model_type}' with class {model_class.__name__}")
        logger.debug(f"Total registered models: {len(cls._models)}")

    @classmethod
    def create_model(cls, model_type: str, config: dict[str, Any] = None) -> BaseAIModel:
        """Create AI model instance."""
        logger.info(f"Creating model instance for type: {model_type}")
        logger.debug(f"Configuration provided: {config is not None}")
        logger.debug(f"Config preview: {repr(config) if config else 'None'}")
        
        key = model_type.strip().lower()
        logger.debug(f"Looking up model with key: {key}")
        logger.debug(f"Available model types: {list(cls._models.keys())}")
        
        model_class = cls._models.get(key)
        if not model_class:
            logger.error(f"Unknown model type requested: {model_type}")
            logger.debug(f"Available models: {list(cls._models.keys())}")
            raise ValueError(f"Unknown model type: {model_type}. Available: {list(cls._models.keys())}")
        
        logger.debug(f"Found model class: {model_class.__name__}")
        logger.debug("Instantiating model with provided configuration")
        
        try:
            model_instance = model_class(config)
            logger.info(f"Successfully created {model_class.__name__} instance")
            logger.debug(f"Model instance type: {type(model_instance).__name__}")
            return model_instance
        except Exception as e:
            logger.error(f"Failed to create model instance of type {model_type}: {str(e)}")
            logger.exception("Full exception details for model creation error:")
            raise

    @classmethod
    def get_available_models(cls) -> list:
        """Get list of available model types."""
        logger.debug("Retrieving list of available model types")
        available_models = list(cls._models.keys())
        logger.debug(f"Available models: {available_models}")
        logger.info(f"Retrieved {len(available_models)} available model types")
        return available_models
