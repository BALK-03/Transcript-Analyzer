import os, sys
from typing import Any

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
from src.services.extraction.base_extractor import BaseExtractor
from src.models.base_model import BaseAIModel
import paths


class AssigneesExtractor(BaseExtractor):
    """Handles extraction of assignees from segments."""
    
    def __init__(self):
        super().__init__(paths.EXTRACTION_ASSIGNEES_PROMPT)
    
    def extract(self, segment: dict[str, Any], model: BaseAIModel, previous_data: dict = None, debug: bool = False) -> dict[str, Any]:
        """
        Extract assignees from the segment.
        """
        try:
            prompt = self._prep_prompt(segment)
            response = model.process(prompt)
            json_response = self._extract_json_from_text(response, "ASSIGNEES" if debug else "")
            
            if not json_response:
                if debug:
                    print(f"WARNING: Failed to extract assignees JSON, using defaults")
                return self.get_default_values()
            
            # Validate expected structure
            if "assignees" not in json_response:
                if debug:
                    print(f"WARNING: Assignees response missing 'assignees' key, using defaults")
                return self.get_default_values()
            
            return json_response
            
        except Exception as e:
            if debug:
                print(f"ERROR in assignees extraction: {str(e)}")
            return self.get_default_values()
    
    def get_default_values(self) -> dict[str, Any]:
        """Return default values when assignees extraction fails."""
        return {"assignees": []}
