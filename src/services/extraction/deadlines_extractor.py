import os, sys
from typing import Any

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
from src.services.extraction.base_extractor import BaseExtractor
from src.models.base_model import BaseAIModel
import paths


class DeadlinesExtractor(BaseExtractor):
    """Handles extraction of deadlines from segments."""
    
    def __init__(self):
        super().__init__(paths.EXTRACTION_DEADLINES_PROMPT)
    
    def extract(self, segment: dict[str, Any], model: BaseAIModel, previous_data: dict = None, debug: bool = False) -> dict[str, Any]:
        """
        Extract deadlines based on segment and previously extracted assignees.
        """
        try:
            prompt = self._prep_prompt(segment, previous_data)
            response = model.process(prompt)
            json_response = self._extract_json_from_text(response, "DEADLINES" if debug else "")
            
            if not json_response:
                if debug:
                    print(f"WARNING: Failed to extract deadlines JSON, using defaults")
                return self.get_default_values()
            
            # Validate expected structure
            if "deadlines" not in json_response:
                json_response["deadlines"] = []
            if "urgent_flags" not in json_response:
                json_response["urgent_flags"] = []
            
            return json_response
            
        except Exception as e:
            if debug:
                print(f"ERROR in deadlines extraction: {str(e)}")
            return self.get_default_values()
    
    def get_default_values(self) -> dict[str, Any]:
        """Return default values when deadlines extraction fails."""
        return {"deadlines": [], "urgent_flags": []}