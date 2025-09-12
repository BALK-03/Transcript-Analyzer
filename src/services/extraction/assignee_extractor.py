from typing import Any
from src.utils.logger import get_logger
from src.services.extraction.base_extractor import BaseExtractor
from src.models.base_model import BaseAIModel
from config import paths

logger = get_logger(__name__)

class AssigneesExtractor(BaseExtractor):
    """Handles extraction of assignees from segments."""
    
    def __init__(self):
        super().__init__(paths.EXTRACTION_ASSIGNEES_PROMPT)
        logger.info("AssigneesExtractor initialized.")
    
    def extract(self, segment: dict[str, Any], model: BaseAIModel, previous_data: dict = None, debug: bool = False) -> dict[str, Any]:
        """
        Extract assignees from the segment.
        """
        segment_id = segment.get('id', 'N/A')
        logger.info(f"Starting assignees extraction for segment ID: {segment_id}")
        
        try:
            prompt = self._prep_prompt(segment)
            logger.debug(f"Generated prompt for segment {segment_id}.")

            logger.info(f"Sending prompt to AI model for segment {segment_id}.")
            response = model.process(prompt)
            logger.debug(f"Received raw response from model for segment {segment_id}.")

            json_response = self._extract_json_from_text(response, "ASSIGNEES" if debug else "")
            
            if not json_response:
                logger.warning(
                    f"Failed to extract valid JSON from the model's response for segment {segment_id}. "
                    f"Falling back to default values."
                )
                return self.get_default_values()
            
            logger.debug(f"Successfully parsed JSON for segment {segment_id}: {json_response}")
            
            # Validate expected structure
            if "assignees" not in json_response:
                logger.warning(
                    f"Assignees JSON for segment {segment_id} is missing the required 'assignees' key. "
                    f"Falling back to default values."
                )
                return self.get_default_values()
            
            logger.info(f"Successfully extracted and validated assignees for segment {segment_id}.")
            return json_response
            
        except Exception as e:
            # logger.exception automatically includes stack trace information in the log
            logger.exception(
                f"An unexpected error occurred during assignees extraction for segment {segment_id}. "
                f"Falling back to default values."
            )
            return self.get_default_values()
    
    def get_default_values(self) -> dict[str, Any]:
        """Return default values when assignees extraction fails."""
        logger.info("Returning default values for assignees.")
        return {"assignees": []}
