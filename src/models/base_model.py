from abc import ABC, abstractmethod
from typing import Dict, Any
from src.utils.logger import get_logger

logger = get_logger(__name__)


class BaseAIModel(ABC):
    def __init__(self, config: Dict[str, Any] = None):
        logger.debug(f"Initializing {self.__class__.__name__}")
        self.config = config or {}
        logger.debug(f"Configuration set: {repr(self.config) if self.config else 'empty config'}")
        logger.info(f"{self.__class__.__name__} successfully initialized")
    
    @abstractmethod
    def process(self, input_text: str) -> str:
        """Main processing method - the core AI logic"""
        pass
    
    @abstractmethod
    def get_info(self) -> Dict[str, str]:
        """Get model information"""
        pass

    def validate_input(self, input_text: Any) -> str:
        """Default validation: ensures input is a non-empty string."""
        logger.debug("Starting input validation")
        logger.debug(f"Input type: {type(input_text)}")
        logger.debug(f"Input preview: {repr(str(input_text)[:100]) if input_text else 'None'}...")
        
        if not isinstance(input_text, str):
            logger.error(f"Input validation failed: expected string, got {type(input_text)}")
            raise TypeError("Input must be a string.")
        
        logger.debug("Input type validation passed")
        input_text = input_text.strip()
        logger.debug(f"Input length after stripping: {len(input_text)} characters")
        
        if not input_text:
            logger.error("Input validation failed: input is empty after stripping")
            raise ValueError("Input cannot be empty.")
        
        if len(input_text) > 1000:
            logger.error(f"Input validation failed: input too long ({len(input_text)} > 1000 characters)")
            raise ValueError("Input is too long (max 1000 characters).")
        
        logger.debug("Input validation completed successfully")
        logger.debug(f"Validated input length: {len(input_text)} characters")
        return input_text
