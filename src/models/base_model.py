from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseAIModel(ABC):
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
    
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
        if not isinstance(input_text, str):
            raise TypeError("Input must be a string.")
        input_text = input_text.strip()
        if not input_text:
            raise ValueError("Input cannot be empty.")
        if len(input_text) > 1000:
            raise ValueError("Input is too long (max 1000 characters).")
        return input_text