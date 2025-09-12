import re
import json
from typing import Optional, Any
from src.models.base_model import BaseAIModel
from src.utils.logger import get_logger
from config import paths

logger = get_logger(__name__)


class ClusteringService:
    def __init__(self):
        logger.debug("Initializing ClusteringService")
        self._prompt_template_filepath = paths.CLUSTERING_SERVICE_PROMPT
        logger.debug(f"Prompt template filepath configured: {self._prompt_template_filepath}")
        logger.info("ClusteringService successfully initialized")

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

    def _prep_prompt(self, chunks: list[dict]) -> str:
        """
        Injects JSON-serialized chunks into the prompt template.

        Replaces 'content' key with 'content' to match prompt expectations.
        """
        logger.debug("Preparing prompt by injecting chunks data into template")
        logger.debug(f"Number of chunks to inject: {len(chunks)}")
        logger.debug(f"Chunks preview: {repr(chunks[:2]) if chunks else 'None'}...")
        
        prompt_template = self._load_prompt_template(filepath=self._prompt_template_filepath)
        logger.debug("Injecting chunks data into prompt template")
        prepared_prompt = prompt_template.format(input_data=json.dumps(chunks, indent=2))
        logger.debug("Prompt successfully prepared with chunks data")
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

    def enrich_segments_with_chunks(
        self,
        segments: dict[str, list[dict[str, Any]]],
        chunks: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Matches chunks to their segments based on chunk_ids and returns enriched segments.
        """
        logger.info("Starting segment enrichment with chunks")
        logger.debug(f"Number of segments to enrich: {len(segments.get('segments', []))}")
        logger.debug(f"Number of chunks available: {len(chunks)}")
        
        logger.debug("Creating chunk mapping by id")
        chunk_map = {chunk["id"]: chunk for chunk in chunks}
        logger.debug(f"Created chunk map with {len(chunk_map)} entries")

        enriched_segments = []
        logger.debug("Starting segment enrichment process")

        for i, segment in enumerate(segments.get("segments", [])):
            logger.debug(f"Processing segment {i}: {segment.get('segment_id', 'unknown')}")
            logger.debug(f"Segment topic summary: {repr(segment.get('topic_summary', 'None')[:100])}...")
            
            chunk_ids = segment.get("chunk_ids", [])
            logger.debug(f"Segment has {len(chunk_ids)} chunk IDs: {chunk_ids}")
            
            matched_chunks = [
                chunk_map[cid] for cid in chunk_ids if cid in chunk_map
            ]
            logger.debug(f"Successfully matched {len(matched_chunks)} chunks for segment {i}")
            
            enriched_segment = {
                "segment_id": segment["segment_id"],
                "topic_summary": segment["topic_summary"],
                "chunks": matched_chunks
            }
            enriched_segments.append(enriched_segment)
            logger.debug(f"Enriched segment {i} created successfully")

        logger.info(f"Segment enrichment completed successfully. Created {len(enriched_segments)} enriched segments")
        logger.debug(f"Total enriched segments: {len(enriched_segments)}")
        return enriched_segments

    def chunks_to_segments(self, chunks: list[dict], model: BaseAIModel) -> list[dict[str, Any]]:
        """
        Sends chunks to the LLM to receive topic-based segments, and enriches them with chunk data.
        """
        logger.info("Starting chunks to segments conversion")
        logger.debug(f"Number of chunks to process: {len(chunks)}")
        logger.debug(f"Chunks preview: {repr(chunks[:2]) if chunks else 'None'}...")
        
        try:
            logger.debug("Preparing prompt for model processing")
            prompt = self._prep_prompt(chunks=chunks)
            logger.debug("Prompt prepared successfully, sending to model")
            
            response = model.process(prompt)
            logger.debug(f"Received response from model: {repr(response[:200])}...")
            
            logger.debug("Attempting to extract JSON from model response")
            json_response = self._extract_json_from_text(response)
            if not json_response:
                logger.error("Model returned invalid JSON format")
                raise ValueError("Model returned invalid JSON format.")
            
            logger.debug("Successfully extracted JSON from model response")
            logger.debug(f"JSON response preview: {repr(json_response)}")
            
            logger.debug("Starting segment enrichment with chunks")
            enriched = self.enrich_segments_with_chunks(json_response, chunks)
            logger.info("Chunks to segments conversion completed successfully")
            logger.debug(f"Final enriched segments count: {len(enriched)}")
            return enriched
            
        except Exception as e:
            logger.error(f"Error occurred during chunks to segments conversion: {str(e)}")
            logger.exception("Full exception details for chunks to segments error:")
            raise Exception("Problem occurred while prompting the model.") from e
