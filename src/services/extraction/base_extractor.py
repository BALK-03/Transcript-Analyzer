import os, sys
from abc import ABC, abstractmethod
import re
from typing import Any, Optional
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
from src.models.base_model import BaseAIModel


class BaseExtractor(ABC):
    """Base class for all extractors with common functionality."""
    
    def __init__(self, prompt_filepath: str):
        self.prompt_filepath = prompt_filepath
    
    def _load_prompt_template(self, filepath: str) -> str:
        """Loads the prompt template from a file."""
        try:
            with open(filepath, 'r') as file:
                prompt = file.read()
            if not prompt.strip():
                raise ValueError("Prompt cannot be empty.")
            return prompt
        except Exception:
            raise ValueError(f"Problem occurred while loading prompt from {filepath}.")

    def _prep_prompt(self, segment: dict[str, Any], extracted_data: dict = None) -> str:
        """
        Injects JSON-serialized segment and previous extraction results into the prompt template.
        """
        prompt_template = self._load_prompt_template(filepath=self.prompt_filepath)
        
        # For first prompt, only inject segment data
        if extracted_data is None:
            return prompt_template.format(segment_data=json.dumps(segment, indent=2))
        else:
            # For subsequent prompts, inject both segment and previous extraction results
            return prompt_template.format(
                segment_data=json.dumps(segment, indent=2),
                extracted_data=json.dumps(extracted_data, indent=2)
            )

    def _extract_json_from_text(self, text: str, debug_step: str = "") -> Optional[dict]:
        """
        Extracts and parses a JSON object from a string that may contain markdown-style code fences.
        Improved with multiple extraction strategies and better debugging.
        """
        # Debug: Print the raw response for troubleshooting
        if debug_step:
            print(f"\n=== DEBUG {debug_step.upper()} ===")
            print(f"Raw response: {repr(text[:500])}")  # First 500 chars
            print("=" * 40)
        
        # Strategy 1: Try to find JSON in code fences
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
        if match:
            json_str = match.group(1).strip()
            try:
                parsed_json = json.loads(json_str)
                if isinstance(parsed_json, dict):
                    return parsed_json
            except json.JSONDecodeError as e:
                if debug_step:
                    print(f"Code fence JSON parse error: {e}")
                    print(f"Attempted to parse: {repr(json_str)}")
        
        # Strategy 2: Try to find JSON without code fences (look for { ... })
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)
        
        for match in matches:
            try:
                parsed_json = json.loads(match.strip())
                if isinstance(parsed_json, dict):
                    return parsed_json
            except json.JSONDecodeError:
                continue
        
        # Strategy 3: More aggressive JSON extraction - look for key patterns
        # Try to find content between first { and last }
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        
        if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
            potential_json = text[start_idx:end_idx + 1]
            try:
                parsed_json = json.loads(potential_json)
                if isinstance(parsed_json, dict):
                    return parsed_json
            except json.JSONDecodeError as e:
                if debug_step:
                    print(f"Aggressive extraction failed: {e}")
                    print(f"Attempted to parse: {repr(potential_json)}")
        
        # If all strategies fail, print debug info
        if debug_step:
            print(f"All JSON extraction strategies failed for {debug_step}")
            print(f"Full response: {repr(text)}")
        
        return None

    @abstractmethod
    def extract(self, segment: dict[str, Any], model: BaseAIModel, previous_data: dict = None, debug: bool = False) -> dict[str, Any]:
        """Abstract method that each extractor must implement."""
        pass

    @abstractmethod
    def get_default_values(self) -> dict[str, Any]:
        """Abstract method to return default values when extraction fails."""
        pass
