import os, sys
from typing import Any
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.services.chunking_service import ChunkingService
from src.services.clustering_service import ClusteringService
from src.services.filtering_service import FilteringService
from src.services.extraction_service import ExtractionService
from src.models.model_factory import AIModelFactory
from config import get_config

def run_pipeline(transcript_input: str, debug: bool = None) -> dict[str, Any]:
    """
    Main pipeline function: takes raw transcript text and returns structured action items.
    Steps:
      1. Chunk transcript
      2. Cluster chunks into segments
      3. Filter segments for actionable content
      4. Extract structured action info from actionable segments
    """
    # Get configuration
    config = get_config()
    
    # Use config's debug mode if not explicitly provided
    if debug is None:
        debug = config.DEBUG_MODE
    
    # Use config's file validation logic
    if config.is_valid_file_path(transcript_input):
        with open(transcript_input, 'r') as f:
            transcript = f.read()
    else:
        transcript = transcript_input

    # 1. Chunking
    chunker = ChunkingService()
    chunks = chunker.transcript_to_chunks(
        transcript,
        start_marker=config.CHUNK_START_MARKER,
        end_marker=config.CHUNK_END_MARKER
    )
    if debug:
        print(f"Chunked {len(chunks)} utterances.")

    # 2. Clustering
    factory = AIModelFactory()
    model = factory.create_model(
        model_type=config.MODEL_TYPE,
        config=config.get_model_config()
    )
    clustering_service = ClusteringService()
    clustered_segments = clustering_service.chunks_to_segments(chunks, model)
    if debug:
        print(f"Clustered into {len(clustered_segments)} segments.")

    # 3. Filtering for actionable segments
    filtering_service = FilteringService()
    actionable_segments = filtering_service.filter_for_actionable_segments(clustered_segments, model)
    if debug:
        print(f"Found {len(actionable_segments)} actionable segments.")

    # 4. Extraction of structured action info
    extraction_service = ExtractionService()
    summary = extraction_service.get_structured_action_summary(actionable_segments, model, debug=debug)

    return summary

if __name__ == "__main__":
    import paths
    from dotenv import load_dotenv
    from pprint import pprint

    load_dotenv(paths.ENV_FILE)
    
    config = get_config()
    
    summary = run_pipeline(
        transcript_input=config.DEFAULT_TRANSCRIPT_FILE,
        debug=config.DEBUG_MODE
    )
    pprint(summary)