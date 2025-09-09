import re
import json
from typing import Optional, Any
from src.models.base_model import BaseAIModel
from config import paths

class FilteringService:
    def __init__(self):
        self._prompt_template_filepath = paths.FILTERING_SERVICE_PROMPT

    def _load_prompt_template(self, filepath: str) -> str:
        """Loads the prompt template from a file."""
        try:
            with open(filepath, 'r') as file:
                prompt = file.read()
            if not prompt.strip():
                raise ValueError("Prompt cannot be empty.")
            return prompt
        except Exception:
            raise ValueError("Problem occurred while loading system prompt.")

    def _prep_prompt(self, segment: dict[str, Any]) -> str:
        """
        Injects JSON-serialized segment into the prompt template.
        """
        prompt_template = self._load_prompt_template(filepath=self._prompt_template_filepath)
        return prompt_template.format(input_data=json.dumps(segment, indent=2))

    def _extract_json_from_text(self, text: str) -> Optional[dict]:
        """
        Extracts and parses a JSON object from a string that may contain markdown-style code fences.
        """
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
        if not match:
            return None

        json_str = match.group(1).strip()

        try:
            parsed_json = json.loads(json_str)
            return parsed_json if isinstance(parsed_json, dict) else None
        except json.JSONDecodeError:
            return None

    def _validate_action_response(self, response: dict) -> bool:
        """
        Validates that the response has the required structure for action detection.
        """
        required_keys = ["action_segments_found", "confidence_percentage", "explanation"]
        
        if not all(key in response for key in required_keys):
            return False
        
        if response["action_segments_found"] not in ["yes", "no"]:
            return False
        
        if not isinstance(response["confidence_percentage"], int) or not (0 <= response["confidence_percentage"] <= 100):
            return False
        
        if not isinstance(response["explanation"], str):
            return False
        
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
        try:
            prompt = self._prep_prompt(segment=segment)
            response = model.process(prompt)
            json_response = self._extract_json_from_text(response)
            
            if not json_response:
                raise ValueError("Model returned invalid JSON format.")
            
            if not self._validate_action_response(json_response):
                raise ValueError("Model returned invalid action analysis structure.")
            
            # Return segment with action analysis
            return {
                "segment_id": segment["segment_id"],
                "topic_summary": segment["topic_summary"],
                "chunks": segment["chunks"],
                "action_analysis": json_response
            }
            
        except Exception as e:
            raise Exception(f"Problem occurred while analyzing segment {segment.get('segment_id', 'unknown')}: {str(e)}") from e

    def filter_segments_for_actions(self, segments: list[dict[str, Any]], model: BaseAIModel) -> list[dict[str, Any]]:
        """
        Analyzes multiple segments to identify which contain actionable content.
        
        Args:
            segments: List of segment dictionaries from ClusteringService
            model: The AI model to use for analysis
            
        Returns:
            List of segments with action analysis results
        """
        analyzed_segments = []
        
        for segment in segments:
            try:
                analyzed_segment = self.analyze_segment_for_actions(segment, model)
                analyzed_segments.append(analyzed_segment)
            except Exception as e:
                # Log error but continue processing other segments
                print(f"Error analyzing segment {segment.get('segment_id', 'unknown')}: {e}")
                # Add segment with error status
                analyzed_segments.append({
                    "segment_id": segment.get("segment_id", "unknown"),
                    "topic_summary": segment.get("topic_summary", ""),
                    "chunks": segment.get("chunks", []),
                    "action_analysis": {
                        "action_segments_found": "no",
                        "confidence_percentage": 0,
                        "explanation": "Error occurred during analysis"
                    }
                })
        
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
        analyzed_segments = self.filter_segments_for_actions(segments, model)
        return [
            segment for segment in analyzed_segments 
            if segment["action_analysis"]["action_segments_found"] == "yes"
        ]

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
        return self.get_actionable_segments_only(segments, model)
