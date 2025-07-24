import os, sys
from typing import Any

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.services.extraction.assignee_extractor import AssigneesExtractor
from src.services.extraction.deadlines_extractor import DeadlinesExtractor
from src.services.extraction.priority_extractor import PriorityExtractor
from src.services.extraction.category_extractor import CategoryExtractor
from src.models.base_model import BaseAIModel
import paths


class ExtractionService:
    """
    Orchestrates the extraction process using specialized extractors.
    Acts as a facade for the four extraction services.
    """
    
    def __init__(self):
        self.assignees_extractor = AssigneesExtractor()
        self.deadlines_extractor = DeadlinesExtractor()
        self.priority_extractor = PriorityExtractor()
        self.category_extractor = CategoryExtractor()

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
        try:
            if debug:
                print(f"\nProcessing segment {segment.get('segment_id', 'unknown')}")
            
            # Step 1: Extract Assignees
            assignees_data = self.assignees_extractor.extract(segment, model, debug=debug)
            if debug:
                print(f"Assignees: {assignees_data}")
            
            # Step 2: Extract Deadlines (using assignees context)
            deadlines_data = self.deadlines_extractor.extract(segment, model, assignees_data, debug=debug)
            if debug:
                print(f"Deadlines: {deadlines_data}")
            
            # Combine data for next step
            combined_data = {**assignees_data, **deadlines_data}
            
            # Step 3: Extract Priority (using previous context)
            priority_data = self.priority_extractor.extract(segment, model, combined_data, debug=debug)
            if debug:
                print(f"Priority: {priority_data}")
            
            # Update combined data
            combined_data.update(priority_data)
            
            # Step 4: Extract Category (using all previous context)
            category_data = self.category_extractor.extract(segment, model, combined_data, debug=debug)
            if debug:
                print(f"Category: {category_data}")
            
            # Convert to clean, flat structure
            return self._format_clean_output(segment, assignees_data, deadlines_data, priority_data, category_data)
            
        except Exception as e:
            print(f"ERROR: Problem occurred while extracting from segment {segment.get('segment_id', 'unknown')}: {str(e)}")
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
        # Extract the main assignee (first one if multiple, or "Unassigned" if none)
        assignees = assignees_data.get("assignees", [])
        main_assignee = assignees[0] if assignees else "Unassigned"
        
        # Extract the main deadline (first one if multiple, or "No deadline" if none)
        deadlines = deadlines_data.get("deadlines", [])
        main_deadline = deadlines[0] if deadlines else "No deadline"
        
        # Get priority level
        priority_level = priority_data.get("priority", "Medium")
        
        # Get category
        category = category_data.get("category", "Other")
        
        # Get task description from topic summary
        task = segment.get("topic_summary", "No task description")
        
        return {
            "task": task,
            "assignee": main_assignee,
            "deadline": main_deadline,
            "priority_level": priority_level,
            "category": category
        }

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
        extracted_segments = []
        
        for segment in segments:
            extracted_segment = self.extract_from_segment(segment, model, debug)
            extracted_segments.append(extracted_segment)
        
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
        extracted_segments = self.extract_from_segments(segments, model, debug)
        
        summary = {
            "total_segments_processed": len(extracted_segments),
            "total_actions": len(extracted_segments),  # Each segment represents one action
            "actions": []  # Changed from "segments_with_actions" to "actions"
        }
        
        for segment in extracted_segments:
            # Since we now return clean format directly, just add to actions list
            # Only include actions that have meaningful data (not all defaults)
            if (segment.get("assignee") != "Unassigned" or 
                segment.get("deadline") != "No deadline" or 
                segment.get("priority_level") != "Medium" or
                segment.get("category") != "Other"):
                summary["actions"].append(segment)
        
        return summary


if __name__ == "__main__":
    import os, sys
    from dotenv import load_dotenv
    from pprint import pprint

    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from src.models.model_factory import AIModelFactory
    import paths

    load_dotenv(paths.ENV_FILE)

    # Example output from FilteringService (actionable segments only)
    example_actionable_segments = [
        {
            'segment_id': 2, 
            'topic_summary': "Planning for next month's product launch and marketing campaign preparation.", 
            'chunks': [
                {'id': 2, 'order': 2, 'content': "Alice: We need to plan for next month's product launch. John, can you prepare the marketing materials by Friday?"}, 
                {'id': 3, 'order': 3, 'content': 'Charlie: The marketing team is already preparing campaign ideas. I will have the first draft ready by Wednesday.'},
                {'id': 4, 'order': 4, 'content': 'Alice: Great! Sarah, please coordinate with the development team for the final testing phase.'}
            ],
            'action_analysis': {
                'action_segments_found': 'yes',
                'confidence_percentage': 95,
                'explanation': 'Multiple specific tasks assigned with deadlines and responsibilities.'
            }
        }
    ]

    factory = AIModelFactory()
    model = factory.create_model(
        model_type="gemini",
        config={
            "api_key": os.getenv("GEMINI_API_KEY"),
            "model": "gemini-2.0-flash",
            "max_retries": 5,
            "base_delay": 1.0,
            "max_delay": 8.0
        }
    )

    extraction_service = ExtractionService()

    try:
        # Extract actions from segments using chain of prompts (with debug enabled)
        # extracted_segments = extraction_service.extract_from_segments(example_actionable_segments, model, debug=True)
        # print("\n" + "="*50)
        # print("EXTRACTED ACTIONS (CLEAN FORMAT):")
        # print("="*50)
        
        # for action in extracted_segments:
        #     print(f"\nTask: {action['task']}")
        #     print(f"Assignee: {action['assignee']}")
        #     print(f"Deadline: {action['deadline']}")
        #     print(f"Priority Level: {action['priority_level']}")
        #     print(f"Category: {action['category']}")

        # # Get structured summary
        # print("\n" + "="*50)
        # print("STRUCTURED SUMMARY:")
        # print("="*50)
        summary = extraction_service.get_structured_action_summary(example_actionable_segments, model, debug=False)
        pprint(summary)

    except Exception as e:
        print(f"Error during extraction: {e}")
        import traceback
        traceback.print_exc()