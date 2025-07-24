import os, sys
import re
import json
from typing import Optional, Any

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.models.base_model import BaseAIModel
import paths


class ClusteringService:
    def __init__(self):
        self._prompt_template_filepath = paths.CLUSTERING_SERVICE_PROMPT

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

    def _prep_prompt(self, chunks: list[dict]) -> str:
        """
        Injects JSON-serialized chunks into the prompt template.

        Replaces 'content' key with 'content' to match prompt expectations.
        """
        prompt_template = self._load_prompt_template(filepath=self._prompt_template_filepath)
        return prompt_template.format(input_data=json.dumps(chunks, indent=2))

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

    def enrich_segments_with_chunks(
        self,
        segments: dict[str, list[dict[str, Any]]],
        chunks: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Matches chunks to their segments based on chunk_ids and returns enriched segments.
        """
        chunk_map = {chunk["id"]: chunk for chunk in chunks}

        enriched_segments = []

        for segment in segments.get("segments", []):
            matched_chunks = [
                chunk_map[cid] for cid in segment.get("chunk_ids", []) if cid in chunk_map
            ]
            enriched_segments.append({
                "segment_id": segment["segment_id"],
                "topic_summary": segment["topic_summary"],
                "chunks": matched_chunks
            })

        return enriched_segments

    def chunks_to_segments(self, chunks: list[dict], model: BaseAIModel) -> list[dict[str, Any]]:
        """
        Sends chunks to the LLM to receive topic-based segments, and enriches them with chunk data.
        """
        try:
            prompt = self._prep_prompt(chunks=chunks)
            response = model.process(prompt)
            json_response = self._extract_json_from_text(response)
            if not json_response:
                raise ValueError("Model returned invalid JSON format.")

            enriched = self.enrich_segments_with_chunks(json_response, chunks)
            return enriched
        except Exception as e:
            raise Exception("Problem occurred while prompting the model.") from e



if __name__ == "__main__":
    import os, sys
    from dotenv import load_dotenv

    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    from src.models.model_factory import AIModelFactory
    import paths

    load_dotenv(paths.ENV_FILE)

    example_chunks = [
        {"id": 0, "order": 0, "content": "Alice: Let's start by reviewing last quarter's performance."},
        {"id": 1, "order": 1, "content": "Bob: Yes, the sales numbers were lower than expected."},
        {"id": 2, "order": 2, "content": "Alice: We also need to plan for next month's product launch."},
        {"id": 3, "order": 3, "content": "Charlie: The marketing team is already preparing campaign ideas."}
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

    clustering_service = ClusteringService()

    try:
        response = clustering_service.chunks_to_segments(example_chunks, model)
        print("Enriched Segmented Response:\n")
        print(response)
    except Exception as e:
        print(f"Error during segmentation: {e}")
