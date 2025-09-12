from typing import Any
from src.utils.logger import get_logger
from src.services.extraction.base_extractor import BaseExtractor
from src.models.base_model import BaseAIModel
from config import paths

logger = get_logger(__name__)

class CategoryExtractor(BaseExtractor):
    """Handles extraction of category from segments."""
    
    def __init__(self):
        super().__init__(paths.EXTRACTION_CATEGORY_PROMPT)
        self.valid_categories = ["Bug Fix", "Feature Development", "Research", "Documentation", "Meeting", "Other"]
        logger.info("CategoryExtractor initialized.")
        logger.debug(f"Valid categories set to: {self.valid_categories}")
    
    def extract(self, segment: dict[str, Any], model: BaseAIModel, previous_data: dict = None, debug: bool = False) -> dict[str, Any]:
        """
        Extract category based on segment and previously extracted data.
        """
        segment_id = segment.get('id', 'N/A')
        logger.info(f"Starting category extraction for segment ID: {segment_id}")

        try:
            prompt = self._prep_prompt(segment, previous_data)
            logger.debug(f"Generated prompt for segment {segment_id}.")

            logger.info(f"Sending prompt to AI model for segment {segment_id}.")
            response = model.process(prompt)
            logger.debug(f"Received raw response from model for segment {segment_id}.")
            
            json_response = self._extract_json_from_text(response, "CATEGORY" if debug else "")
            
            if not json_response:
                logger.warning(
                    f"Failed to extract valid JSON from model's response for segment {segment_id}. "
                    f"Falling back to default values."
                )
                return self.get_default_values()
            
            logger.debug(f"Successfully parsed JSON for segment {segment_id}: {json_response}")
            
            # Validate expected structure and values
            original_category = json_response.get("category")
            if not original_category or original_category not in self.valid_categories:
                logger.warning(
                    f"Invalid or missing 'category' for segment {segment_id}. "
                    f"Received: '{original_category}'. Setting to 'Other'."
                )
                json_response["category"] = "Other"

            original_confidence = json_response.get("confidence")
            if "confidence" not in json_response or not isinstance(original_confidence, int):
                logger.warning(
                    f"Invalid or missing 'confidence' for segment {segment_id}. "
                    f"Received: '{original_confidence}'. Setting to 50."
                )
                json_response["confidence"] = 50
            
            if "reasoning" not in json_response:
                logger.info(f"Missing 'reasoning' for segment {segment_id}. Setting to default message.")
                json_response["reasoning"] = "Category assessment completed"
            
            logger.info(f"Successfully extracted and validated category for segment {segment_id}.")
            return json_response
            
        except Exception as e:
            logger.exception(
                f"An unexpected error occurred during category extraction for segment {segment_id}. "
                f"Falling back to default values."
            )
            return self.get_default_values()
    
    def get_default_values(self) -> dict[str, Any]:
        """Return default values when category extraction fails."""
        logger.info("Returning default values for category due to an earlier failure.")
        return {
            "category": "Other", 
            "confidence": 50, 
            "reasoning": "Default due to extraction failure"
        }