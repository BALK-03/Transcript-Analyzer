import re
import json
from typing import Optional, Any
from src.models.base_model import BaseAIModel
from src.utils.logger import get_logger
from config import paths

logger = get_logger(__name__)


class FilteringService:
    def __init__(self):
        logger.debug("Initializing FilteringService")
        self._prompt_template_filepath = paths.FILTERING_SERVICE_PROMPT
        logger.debug(f"Prompt template filepath configured: {self._prompt_template_filepath}")
        logger.info("FilteringService successfully initialized")

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
        except Exception as e:
            logger.error(f"Problem occurred while loading system prompt from {filepath}: {str(e)}")
            logger.exception("Full exception details for prompt loading error:")
            raise ValueError("Problem occurred while loading system prompt.")

    def _prep_prompt(self, segment: dict[str, Any]) -> str:
        """
        Injects JSON-serialized segment into the prompt template.
        """
        logger.debug("Preparing prompt by injecting segment data into template")
        logger.debug(f"Segment data: {repr(segment)}")
        
        prompt_template = self._load_prompt_template(filepath=self._prompt_template_filepath)
        logger.debug("Injecting segment data into prompt template")
        prepared_prompt = prompt_template.format(input_data=json.dumps(segment, indent=2))
        logger.debug("Prompt successfully prepared with segment data")
        return prepared_prompt

    def _extract_json_from_text(self, text: str) -> Optional[dict]:
        """
        Extracts and parses a JSON object from a string that may contain markdown-style code fences.
        """
        logger.debug("Starting JSON extraction from text")
        logger.debug(f"Raw text for extraction: {repr(text[:200])}...")
        
        logger.debug("Attempting to find JSON in markdown code fence")
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
        if not match:
            logger.warning("No JSON code fence found in text")
            return None

        json_str = match.group(1).strip()
        logger.debug(f"Extracted JSON string from code fence: {repr(json_str[:200])}...")

        try:
            parsed_json = json.loads(json_str)
            if isinstance(parsed_json, dict):
                logger.debug("Successfully parsed JSON from code fence")
                return parsed_json
            else:
                logger.warning("Parsed JSON is not a dictionary")
                return None
        except json.JSONDecodeError as e:
            logger.warning(f"Could not parse JSON from code fence. Error: {e}")
            logger.debug(f"Invalid JSON string: {repr(json_str)}")
            return None

    def _validate_action_response(self, response: dict) -> bool:
        """
        Validates that the response has the required structure for action detection.
        """
        logger.debug("Validating action response structure")
        logger.debug(f"Response to validate: {repr(response)}")
        
        required_keys = ["action_segments_found", "confidence_percentage", "explanation"]
        logger.debug(f"Required keys: {required_keys}")
        
        if not all(key in response for key in required_keys):
            missing_keys = [key for key in required_keys if key not in response]
            logger.warning(f"Missing required keys in response: {missing_keys}")
            return False
        
        if response["action_segments_found"] not in ["yes", "no"]:
            logger.warning(f"Invalid action_segments_found value: {response['action_segments_found']}")
            return False
        
        if not isinstance(response["confidence_percentage"], int) or not (0 <= response["confidence_percentage"] <= 100):
            logger.warning(f"Invalid confidence_percentage value: {response['confidence_percentage']}")
            return False
        
        if not isinstance(response["explanation"], str):
            logger.warning(f"Invalid explanation value type: {type(response['explanation'])}")
            return False
        
        logger.debug("Action response validation successful")
        return True

    def analyze_segment_for_actions(self, segment: dict[str, Any], model: BaseAIModel) -> dict[str, Any]:
        """
        Analyzes a single segment to determine if it contains actionable content.
        
        Args:
            segment: A segment dictionary with segment_id, topic_summary, and chunks
            model: The AI model to use for analysis
            
        Returns:
            Dictionary with action analysis results including original segment data
        """
        segment_id = segment.get("segment_id", "unknown")
        logger.info(f"Starting action analysis for segment {segment_id}")
        logger.debug(f"Segment data: {repr(segment)}")
        
        try:
            logger.debug("Preparing prompt for action analysis")
            prompt = self._prep_prompt(segment=segment)
            logger.debug("Prompt prepared successfully, sending to model")
            
            response = model.process(prompt)
            logger.debug(f"Received response from model: {repr(response[:200])}...")
            
            logger.debug("Attempting to extract JSON from model response")
            json_response = self._extract_json_from_text(response)
            
            if not json_response:
                logger.error("Model returned invalid JSON format")
                raise ValueError("Model returned invalid JSON format.")
            
            logger.debug("Successfully extracted JSON from model response")
            logger.debug(f"JSON response: {repr(json_response)}")
            
            if not self._validate_action_response(json_response):
                logger.error("Model returned invalid action analysis structure")
                raise ValueError("Model returned invalid action analysis structure.")
            
            logger.debug("Action response validation successful")
            # Return segment with action analysis
            result = {
                "segment_id": segment["segment_id"],
                "topic_summary": segment["topic_summary"],
                "chunks": segment["chunks"],
                "action_analysis": json_response
            }
            logger.info(f"Action analysis for segment {segment_id} completed successfully")
            logger.debug(f"Analysis result - action found: {json_response['action_segments_found']}, confidence: {json_response['confidence_percentage']}%")
            return result
            
        except Exception as e:
            logger.error(f"Error occurred while analyzing segment {segment_id}: {str(e)}")
            logger.exception("Full exception details for segment analysis error:")
            raise Exception(f"Problem occurred while analyzing segment {segment_id}: {str(e)}") from e

    def filter_segments_for_actions(self, segments: list[dict[str, Any]], model: BaseAIModel) -> list[dict[str, Any]]:
        """
        Analyzes multiple segments to identify which contain actionable content.
        
        Args:
            segments: List of segment dictionaries from ClusteringService
            model: The AI model to use for analysis
            
        Returns:
            List of segments with action analysis results
        """
        logger.info(f"Starting action filtering for {len(segments)} segments")
        logger.debug(f"Segments to analyze: {[s.get('segment_id', 'unknown') for s in segments]}")
        
        analyzed_segments = []
        successful_analyses = 0
        failed_analyses = 0
        
        for i, segment in enumerate(segments):
            segment_id = segment.get("segment_id", "unknown")
            logger.debug(f"Processing segment {i + 1} of {len(segments)}: {segment_id}")
            
            try:
                analyzed_segment = self.analyze_segment_for_actions(segment, model)
                analyzed_segments.append(analyzed_segment)
                successful_analyses += 1
                logger.debug(f"Segment {segment_id} analysis completed successfully")
            except Exception as e:
                failed_analyses += 1
                logger.error(f"Error analyzing segment {segment_id}: {e}")
                logger.debug("Adding segment with error status")
                # Log error but continue processing other segments
                print(f"Error analyzing segment {segment_id}: {e}")
                # Add segment with error status
                error_segment = {
                    "segment_id": segment.get("segment_id", "unknown"),
                    "topic_summary": segment.get("topic_summary", ""),
                    "chunks": segment.get("chunks", []),
                    "action_analysis": {
                        "action_segments_found": "no",
                        "confidence_percentage": 0,
                        "explanation": "Error occurred during analysis"
                    }
                }
                analyzed_segments.append(error_segment)
                logger.debug(f"Error segment created for {segment_id}")
        
        logger.info(f"Action filtering completed. {successful_analyses} successful, {failed_analyses} failed out of {len(segments)} total segments")
        logger.debug(f"Total analyzed segments: {len(analyzed_segments)}")
        return analyzed_segments

    def get_actionable_segments_only(self, segments: list[dict[str, Any]], model: BaseAIModel) -> list[dict[str, Any]]:
        """
        Returns only segments that contain actionable content.
        
        Args:
            segments: List of segment dictionaries from ClusteringService
            model: The AI model to use for analysis
            
        Returns:
            List of segments that were identified as containing actions
        """
        logger.info(f"Getting actionable segments only from {len(segments)} segments")
        
        analyzed_segments = self.filter_segments_for_actions(segments, model)
        logger.debug("Filtering analyzed segments for actionable content only")
        
        actionable_segments = [
            segment for segment in analyzed_segments 
            if segment["action_analysis"]["action_segments_found"] == "yes"
        ]
        
        logger.info(f"Found {len(actionable_segments)} actionable segments out of {len(analyzed_segments)} analyzed segments")
        logger.debug(f"Actionable segment IDs: {[s.get('segment_id', 'unknown') for s in actionable_segments]}")
        return actionable_segments

    def filter_for_actionable_segments(self, segments: list[dict[str, Any]], model: BaseAIModel) -> list[dict[str, Any]]:
        """
        Main filtering function that returns only segments predicted as containing actions ("yes").
        This is the primary function to use when you only want actionable segments in the final output.
        
        Args:
            segments: List of segment dictionaries from ClusteringService
            model: The AI model to use for analysis
            
        Returns:
            List containing only segments where action_segments_found == "yes"
        """
        logger.info(f"Starting main filtering for actionable segments from {len(segments)} segments")
        result = self.get_actionable_segments_only(segments, model)
        logger.info(f"Main filtering completed, returning {len(result)} actionable segments")
        return result