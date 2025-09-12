import re
import json
from typing import Any, Optional
from abc import ABC, abstractmethod

from src.utils.logger import get_logger
from src.models.base_model import BaseAIModel

logger = get_logger(__name__)

class BaseExtractor(ABC):
    """Base class for all extractors with common functionality."""
    
    def __init__(self, prompt_filepath: str):
        self.prompt_filepath = prompt_filepath
        logger.info(f"{self.__class__.__name__} initialized with prompt: {prompt_filepath}")
    
    def _load_prompt_template(self, filepath: str) -> str:
        """Loads the prompt template from a file."""
        logger.debug(f"Attempting to load prompt template from: {filepath}")
        try:
            with open(filepath, 'r') as file:
                prompt = file.read()
            if not prompt.strip():
                logger.error(f"Prompt file is empty: {filepath}")
                raise ValueError("Prompt cannot be empty.")
            logger.debug(f"Successfully loaded prompt template from: {filepath}")
            return prompt
        except FileNotFoundError:
            logger.error(f"Prompt file not found at path: {filepath}")
            raise
        except Exception as e:
            # Log the original exception with its traceback for better debugging
            logger.exception(f"An unexpected error occurred while loading prompt from {filepath}.")
            raise ValueError(f"Problem occurred while loading prompt from {filepath}.")

    def _prep_prompt(self, segment: dict[str, Any], extracted_data: dict = None) -> str:
        """
        Injects JSON-serialized segment and previous extraction results into the prompt template.
        """
        logger.debug("Preparing prompt by injecting data into the template.")
        prompt_template = self._load_prompt_template(filepath=self.prompt_filepath)
        
        # For first prompt, only inject segment data
        if extracted_data is None:
            logger.debug("Injecting segment data only into prompt.")
            return prompt_template.format(segment_data=json.dumps(segment, indent=2))
        else:
            # For subsequent prompts, inject both segment and previous extraction results
            logger.debug("Injecting both segment data and previous extraction results into prompt.")
            return prompt_template.format(
                segment_data=json.dumps(segment, indent=2),
                extracted_data=json.dumps(extracted_data, indent=2)
            )

    def _extract_json_from_text(self, text: str, debug_step: str = "") -> Optional[dict]:
        """
        Extracts and parses a JSON object from a string that may contain markdown-style code fences.
        """
        context = f" (Context: {debug_step})" if debug_step else ""
        logger.info(f"Starting JSON extraction from text{context}.")
        logger.debug(f"Raw text for extraction{context}: {repr(text[:500])}...")

        # Strategy 1: Try to find JSON in code fences
        logger.debug(f"Attempting Strategy 1: Find JSON in markdown code fence{context}.")
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
        if match:
            json_str = match.group(1).strip()
            try:
                parsed_json = json.loads(json_str)
                if isinstance(parsed_json, dict):
                    logger.info(f"Strategy 1 successful: Parsed JSON from code fence{context}.")
                    return parsed_json
            except json.JSONDecodeError as e:
                logger.warning(f"Strategy 1 failed: Could not parse JSON from code fence{context}. Error: {e}")
                logger.debug(f"Invalid JSON string from code fence: {repr(json_str)}")
        
        # Strategy 2: Try to find JSON without code fences (look for { ... })
        logger.debug(f"Attempting Strategy 2: Find first valid top-level JSON object{context}.")
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)
        for potential_json in matches:
            try:
                parsed_json = json.loads(potential_json.strip())
                if isinstance(parsed_json, dict):
                    logger.info(f"Strategy 2 successful: Parsed a standalone JSON object{context}.")
                    return parsed_json
            except json.JSONDecodeError:
                continue
        
        # Strategy 3: Aggressive extraction - find content between first { and last }
        logger.debug(f"Attempting Strategy 3: Aggressively find content between first '{{' and last '}}'{context}.")
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
            potential_json = text[start_idx:end_idx + 1]
            try:
                parsed_json = json.loads(potential_json)
                if isinstance(parsed_json, dict):
                    logger.info(f"Strategy 3 successful: Parsed JSON via aggressive extraction{context}.")
                    return parsed_json
            except json.JSONDecodeError as e:
                logger.warning(f"Strategy 3 failed: Could not parse content{context}. Error: {e}")
                logger.debug(f"Invalid content from aggressive extraction: {repr(potential_json)}")

        logger.error(f"All JSON extraction strategies failed{context}.")
        return None

    @abstractmethod
    def extract(self, segment: dict[str, Any], model: BaseAIModel, previous_data: dict = None, debug: bool = False) -> dict[str, Any]:
        """Abstract method that each extractor must implement."""
        pass

    @abstractmethod
    def get_default_values(self) -> dict[str, Any]:
        """Abstract method to return default values when extraction fails."""
        pass
