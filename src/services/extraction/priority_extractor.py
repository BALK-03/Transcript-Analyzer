from typing import Any
from src.services.extraction.base_extractor import BaseExtractor
from src.models.base_model import BaseAIModel
from src.utils.logger import get_logger
from config import paths

logger = get_logger(__name__)


class PriorityExtractor(BaseExtractor):
    """Handles extraction of priority from segments."""
    
    def __init__(self):
        logger.debug("Initializing PriorityExtractor")
        super().__init__(paths.EXTRACTION_PRIORITY_PROMPT)
        self.valid_priorities = ["High", "Medium", "Low"]
        logger.debug(f"Valid priorities configured: {self.valid_priorities}")
        logger.info("PriorityExtractor successfully initialized")
    
    def extract(self, segment: dict[str, Any], model: BaseAIModel, previous_data: dict = None, debug: bool = False) -> dict[str, Any]:
        """
        Extract priority based on segment and previously extracted data.
        """
        logger.info("Starting priority extraction from segment")
        logger.debug(f"Segment data for extraction: {repr(segment)}")
        logger.debug(f"Previous data available: {previous_data is not None}")
        logger.debug(f"Debug mode enabled: {debug}")
        
        try:
            logger.debug("Preparing prompt for priority extraction")
            prompt = self._prep_prompt(segment, previous_data)
            logger.debug("Prompt successfully prepared, sending to model for processing")
            
            response = model.process(prompt)
            logger.debug(f"Received response from model: {repr(response[:200])}...")
            
            logger.debug("Attempting to extract JSON from model response")
            json_response = self._extract_json_from_text(response, "PRIORITY" if debug else "")
            
            if not json_response:
                logger.warning("Failed to extract priority JSON from model response, using default values")
                if debug:
                    print(f"WARNING: Failed to extract priority JSON, using defaults")
                return self.get_default_values()
            
            logger.debug(f"Successfully extracted JSON response: {repr(json_response)}")
            logger.debug("Validating expected structure and values in extracted JSON")
            
            # Validate expected structure and values
            if "priority" not in json_response or json_response["priority"] not in self.valid_priorities:
                logger.debug(f"Invalid or missing priority value: {json_response.get('priority', 'None')}, setting to default 'Medium'")
                json_response["priority"] = "Medium"
            else:
                logger.debug(f"Valid priority value found: {json_response['priority']}")
            
            if "confidence" not in json_response or not isinstance(json_response["confidence"], int):
                logger.debug(f"Invalid or missing confidence value: {json_response.get('confidence', 'None')}, setting to default 50")
                json_response["confidence"] = 50
            else:
                logger.debug(f"Valid confidence value found: {json_response['confidence']}")
            
            if "reasoning" not in json_response:
                logger.debug("Missing reasoning field, adding default reasoning")
                json_response["reasoning"] = "Priority assessment completed"
            else:
                logger.debug(f"Reasoning field found: {repr(json_response['reasoning'][:100])}...")
            
            logger.info("Priority extraction completed successfully")
            logger.debug(f"Final extracted priority data: {repr(json_response)}")
            return json_response
            
        except Exception as e:
            logger.error(f"Error occurred during priority extraction: {str(e)}")
            logger.exception("Full exception details for priority extraction error:")
            if debug:
                print(f"ERROR in priority extraction: {str(e)}")
            logger.info("Returning default values due to extraction error")
            return self.get_default_values()
    
    def get_default_values(self) -> dict[str, Any]:
        """Return default values when priority extraction fails."""
        logger.debug("Returning default values for priority extraction")
        default_values = {
            "priority": "Medium", 
            "confidence": 50, 
            "reasoning": "Default due to extraction failure"
        }
        logger.debug(f"Default priority values: {repr(default_values)}")
        return default_values
