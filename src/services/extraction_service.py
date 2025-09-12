from typing import Any

from src.services.extraction.assignee_extractor import AssigneesExtractor
from src.services.extraction.deadlines_extractor import DeadlinesExtractor
from src.services.extraction.priority_extractor import PriorityExtractor
from src.services.extraction.category_extractor import CategoryExtractor
from src.models.base_model import BaseAIModel
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ExtractionService:
    """
    Orchestrates the extraction process using specialized extractors.
    Acts as a facade for the four extraction services.
    """
    
    def __init__(self):
        logger.debug("Initializing ExtractionService")
        self.assignees_extractor = AssigneesExtractor()
        logger.debug("AssigneesExtractor initialized")
        self.deadlines_extractor = DeadlinesExtractor()
        logger.debug("DeadlinesExtractor initialized")
        self.priority_extractor = PriorityExtractor()
        logger.debug("PriorityExtractor initialized")
        self.category_extractor = CategoryExtractor()
        logger.debug("CategoryExtractor initialized")
        logger.info("ExtractionService successfully initialized with all extractors")

    def extract_from_segment(self, segment: dict[str, Any], model: BaseAIModel, debug: bool = False) -> dict[str, Any]:
        """
        Performs chain of prompts extraction on a single segment.
        Each segment represents an action, so we extract assignees, deadlines, priority, and category.
        
        Args:
            segment: A segment dictionary from FilteringService (represents an action)
            model: The AI model to use for extraction
            debug: Whether to enable debug output
            
        Returns:
            Clean, flat JSON with task, assignee, deadline, priority_level, and category
        """
        segment_id = segment.get('segment_id', 'unknown')
        logger.info(f"Starting extraction from segment {segment_id}")
        logger.debug(f"Segment data: {repr(segment)}")
        logger.debug(f"Debug mode enabled: {debug}")
        
        try:
            if debug:
                print(f"\nProcessing segment {segment_id}")
            
            # Step 1: Extract Assignees
            logger.debug("Step 1: Starting assignees extraction")
            assignees_data = self.assignees_extractor.extract(segment, model, debug=debug)
            logger.debug(f"Assignees extraction completed: {repr(assignees_data)}")
            if debug:
                print(f"Assignees: {assignees_data}")
            
            # Step 2: Extract Deadlines (using assignees context)
            logger.debug("Step 2: Starting deadlines extraction with assignees context")
            deadlines_data = self.deadlines_extractor.extract(segment, model, assignees_data, debug=debug)
            logger.debug(f"Deadlines extraction completed: {repr(deadlines_data)}")
            if debug:
                print(f"Deadlines: {deadlines_data}")
            
            # Combine data for next step
            logger.debug("Combining assignees and deadlines data for next extraction step")
            combined_data = {**assignees_data, **deadlines_data}
            logger.debug(f"Combined data: {repr(combined_data)}")
            
            # Step 3: Extract Priority (using previous context)
            logger.debug("Step 3: Starting priority extraction with combined context")
            priority_data = self.priority_extractor.extract(segment, model, combined_data, debug=debug)
            logger.debug(f"Priority extraction completed: {repr(priority_data)}")
            if debug:
                print(f"Priority: {priority_data}")
            
            # Update combined data
            logger.debug("Updating combined data with priority information")
            combined_data.update(priority_data)
            logger.debug(f"Updated combined data: {repr(combined_data)}")
            
            # Step 4: Extract Category (using all previous context)
            logger.debug("Step 4: Starting category extraction with full context")
            category_data = self.category_extractor.extract(segment, model, combined_data, debug=debug)
            logger.debug(f"Category extraction completed: {repr(category_data)}")
            if debug:
                print(f"Category: {category_data}")
            
            # Convert to clean, flat structure
            logger.debug("Formatting extracted data into clean output structure")
            clean_output = self._format_clean_output(segment, assignees_data, deadlines_data, priority_data, category_data)
            logger.info(f"Extraction from segment {segment_id} completed successfully")
            logger.debug(f"Final clean output: {repr(clean_output)}")
            return clean_output
            
        except Exception as e:
            logger.error(f"Error occurred while extracting from segment {segment_id}: {str(e)}")
            logger.exception("Full exception details for segment extraction error:")
            print(f"ERROR: Problem occurred while extracting from segment {segment_id}: {str(e)}")
            
            logger.info(f"Returning clean structure with default values for segment {segment_id}")
            # Return clean structure with default values
            return self._format_clean_output(
                segment, 
                self.assignees_extractor.get_default_values(),
                self.deadlines_extractor.get_default_values(),
                self.priority_extractor.get_default_values(),
                self.category_extractor.get_default_values()
            )

    def _format_clean_output(self, segment: dict[str, Any], assignees_data: dict, deadlines_data: dict, 
                           priority_data: dict, category_data: dict) -> dict[str, Any]:
        """
        Formats the extracted data into a clean, flat JSON structure.
        
        Returns:
            Clean JSON with: task, assignee, deadline, priority_level, category
        """
        logger.debug("Formatting extracted data into clean output structure")
        logger.debug(f"Input data - assignees: {repr(assignees_data)}, deadlines: {repr(deadlines_data)}, priority: {repr(priority_data)}, category: {repr(category_data)}")
        
        # Extract the main assignee (first one if multiple, or "Unassigned" if none)
        assignees = assignees_data.get("assignees", [])
        main_assignee = assignees[0] if assignees else "Unassigned"
        logger.debug(f"Main assignee determined: {main_assignee} (from {len(assignees)} total assignees)")
        
        # Extract the main deadline (first one if multiple, or "No deadline" if none)
        deadlines = deadlines_data.get("deadlines", [])
        main_deadline = deadlines[0] if deadlines else "No deadline"
        logger.debug(f"Main deadline determined: {main_deadline} (from {len(deadlines)} total deadlines)")
        
        # Get priority level
        priority_level = priority_data.get("priority", "Medium")
        logger.debug(f"Priority level: {priority_level}")
        
        # Get category
        category = category_data.get("category", "Other")
        logger.debug(f"Category: {category}")
        
        # Get task description from topic summary
        task = segment.get("topic_summary", "No task description")
        logger.debug(f"Task description: {repr(task[:100])}...")
        
        clean_output = {
            "task": task,
            "assignee": main_assignee,
            "deadline": main_deadline,
            "priority_level": priority_level,
            "category": category
        }
        
        logger.debug(f"Clean output structure created: {repr(clean_output)}")
        return clean_output

    def extract_from_segments(self, segments: list[dict[str, Any]], model: BaseAIModel, debug: bool = False) -> list[dict[str, Any]]:
        """
        Performs chain of prompts extraction on multiple segments.
        
        Args:
            segments: List of segment dictionaries from FilteringService
            model: The AI model to use for extraction
            debug: Whether to enable debug output
            
        Returns:
            List of segments with extracted action information
        """
        logger.info(f"Starting extraction from {len(segments)} segments")
        logger.debug(f"Debug mode enabled: {debug}")
        
        extracted_segments = []
        
        for i, segment in enumerate(segments):
            logger.debug(f"Processing segment {i + 1} of {len(segments)}: {segment.get('segment_id', 'unknown')}")
            extracted_segment = self.extract_from_segment(segment, model, debug)
            extracted_segments.append(extracted_segment)
            logger.debug(f"Segment {i + 1} extraction completed")
        
        logger.info(f"Extraction from {len(segments)} segments completed successfully")
        logger.debug(f"Total extracted segments: {len(extracted_segments)}")
        return extracted_segments

    def get_structured_action_summary(self, segments: list[dict[str, Any]], model: BaseAIModel, debug: bool = False) -> dict[str, Any]:
        """
        Extract actions from segments and return a structured summary with clean format.
        
        Args:
            segments: List of segment dictionaries from FilteringService
            model: The AI model to use for extraction
            debug: Whether to enable debug output
            
        Returns:
            Structured summary with clean, flat action objects
        """
        logger.info(f"Starting structured action summary extraction from {len(segments)} segments")
        logger.debug(f"Debug mode enabled: {debug}")
        
        extracted_segments = self.extract_from_segments(segments, model, debug)
        logger.debug("All segments extracted, creating structured summary")
        
        summary = {
            "total_segments_processed": len(extracted_segments),
            "total_actions": len(extracted_segments),  # Each segment represents one action
            "actions": []  # Changed from "segments_with_actions" to "actions"
        }
        logger.debug(f"Initial summary structure created with {len(extracted_segments)} total segments/actions")
        
        meaningful_actions_count = 0
        for i, segment in enumerate(extracted_segments):
            logger.debug(f"Evaluating segment {i + 1} for meaningful action data")
            # Since we now return clean format directly, just add to actions list
            # Only include actions that have meaningful data (not all defaults)
            if (segment.get("assignee") != "Unassigned" or 
                segment.get("deadline") != "No deadline" or 
                segment.get("priority_level") != "Medium" or
                segment.get("category") != "Other"):
                summary["actions"].append(segment)
                meaningful_actions_count += 1
                logger.debug(f"Segment {i + 1} added as meaningful action")
            else:
                logger.debug(f"Segment {i + 1} skipped (all default values)")
        
        logger.info(f"Structured action summary completed. {meaningful_actions_count} meaningful actions out of {len(extracted_segments)} total segments")
        logger.debug(f"Final summary structure: {len(summary['actions'])} actions included")
        return summary
