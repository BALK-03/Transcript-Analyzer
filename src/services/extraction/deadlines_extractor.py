from typing import Any
from src.services.extraction.base_extractor import BaseExtractor
from src.models.base_model import BaseAIModel
from src.utils.logger import get_logger
from config import paths

logger = get_logger(__name__)


class DeadlinesExtractor(BaseExtractor):
    """Handles extraction of deadlines from segments."""
    
    def __init__(self):
        logger.debug("Initializing DeadlinesExtractor")
        super().__init__(paths.EXTRACTION_DEADLINES_PROMPT)
        logger.info("DeadlinesExtractor successfully initialized")
    
    def extract(self, segment: dict[str, Any], model: BaseAIModel, previous_data: dict = None, debug: bool = False) -> dict[str, Any]:
        """
        Extract deadlines based on segment and previously extracted assignees.
        """
        logger.info("Starting deadlines extraction from segment")
        logger.debug(f"Segment data for extraction: {repr(segment)}")
        logger.debug(f"Previous data available: {previous_data is not None}")
        logger.debug(f"Debug mode enabled: {debug}")
        
        try:
            logger.debug("Preparing prompt for deadlines extraction")
            prompt = self._prep_prompt(segment, previous_data)
            logger.debug("Prompt successfully prepared, sending to model for processing")
            
            response = model.process(prompt)
            logger.debug(f"Received response from model: {repr(response[:200])}...")
            
            logger.debug("Attempting to extract JSON from model response")
            json_response = self._extract_json_from_text(response, "DEADLINES" if debug else "")
            
            if not json_response:
                logger.warning("Failed to extract deadlines JSON from model response, using default values")
                if debug:
                    print(f"WARNING: Failed to extract deadlines JSON, using defaults")
                return self.get_default_values()
            
            logger.debug(f"Successfully extracted JSON response: {repr(json_response)}")
            logger.debug("Validating expected structure in extracted JSON")
            
            # Validate expected structure
            if "deadlines" not in json_response:
                logger.debug("Missing 'deadlines' field in response, adding empty list")
                json_response["deadlines"] = []
            if "urgent_flags" not in json_response:
                logger.debug("Missing 'urgent_flags' field in response, adding empty list")
                json_response["urgent_flags"] = []
            
            logger.info("Deadlines extraction completed successfully")
            logger.debug(f"Final extracted deadlines data: {repr(json_response)}")
            return json_response
            
        except Exception as e:
            logger.error(f"Error occurred during deadlines extraction: {str(e)}")
            logger.exception("Full exception details for deadlines extraction error:")
            if debug:
                print(f"ERROR in deadlines extraction: {str(e)}")
            logger.info("Returning default values due to extraction error")
            return self.get_default_values()
    
    def get_default_values(self) -> dict[str, Any]:
        """Return default values when deadlines extraction fails."""
        logger.debug("Returning default values for deadlines extraction")
        default_values = {"deadlines": [], "urgent_flags": []}
        logger.debug(f"Default deadlines values: {repr(default_values)}")
        return default_values
