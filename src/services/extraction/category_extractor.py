import os, sys
from typing import Any

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
from src.services.extraction.base_extractor import BaseExtractor
from src.models.base_model import BaseAIModel
import paths

class CategoryExtractor(BaseExtractor):
    """Handles extraction of category from segments."""
    
    def __init__(self):
        super().__init__(paths.EXTRACTION_CATEGORY_PROMPT)
        self.valid_categories = ["Bug Fix", "Feature Development", "Research", "Documentation", "Meeting", "Other"]
    
    def extract(self, segment: dict[str, Any], model: BaseAIModel, previous_data: dict = None, debug: bool = False) -> dict[str, Any]:
        """
        Extract category based on segment and previously extracted data.
        """
        try:
            prompt = self._prep_prompt(segment, previous_data)
            response = model.process(prompt)
            json_response = self._extract_json_from_text(response, "CATEGORY" if debug else "")
            
            if not json_response:
                if debug:
                    print(f"WARNING: Failed to extract category JSON, using defaults")
                return self.get_default_values()
            
            # Validate expected structure and values
            if "category" not in json_response or json_response["category"] not in self.valid_categories:
                json_response["category"] = "Other"
            
            if "confidence" not in json_response or not isinstance(json_response["confidence"], int):
                json_response["confidence"] = 50
            
            if "reasoning" not in json_response:
                json_response["reasoning"] = "Category assessment completed"
            
            return json_response
            
        except Exception as e:
            if debug:
                print(f"ERROR in category extraction: {str(e)}")
            return self.get_default_values()
    
    def get_default_values(self) -> dict[str, Any]:
        """Return default values when category extraction fails."""
        return {
            "category": "Other", 
            "confidence": 50, 
            "reasoning": "Default due to extraction failure"
        }