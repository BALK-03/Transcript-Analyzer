from typing import Any
from src.services.chunking_service import ChunkingService
from src.services.clustering_service import ClusteringService
from src.services.filtering_service import FilteringService
from src.services.extraction_service import ExtractionService
from src.models.model_factory import AIModelFactory
import src.models.register_all_models # Important to register models
from src.utils.logger import get_logger
from config.config import get_config

logger = get_logger(__name__)


def run_pipeline(transcript_input: str, debug: bool = None) -> dict[str, Any]:
    """
    Main pipeline function: takes raw transcript text and returns structured action items.
    Steps:
      1. Chunk transcript
      2. Cluster chunks into segments
      3. Filter segments for actionable content
      4. Extract structured action info from actionable segments
    """
    logger.info("Starting action extraction pipeline")
    logger.debug(f"Transcript input type: {'file path' if transcript_input.endswith(('.txt', '.md')) else 'direct text'}")
    logger.debug(f"Debug parameter provided: {debug}")
    
    # Get configuration
    logger.debug("Loading pipeline configuration")
    config = get_config()
    logger.debug("Configuration loaded successfully")
    
    # Use config's debug mode if not explicitly provided
    if debug is None:
        debug = config.DEBUG_MODE
        logger.debug(f"Using debug mode from configuration: {debug}")
    else:
        logger.debug(f"Using provided debug mode: {debug}")
    
    # Use config's file validation logic
    logger.debug("Determining input type and loading transcript content")
    if config.is_valid_file_path(transcript_input):
        logger.debug(f"Input detected as file path: {transcript_input}")
        try:
            with open(transcript_input, 'r') as f:
                transcript = f.read()
            logger.debug(f"Successfully loaded transcript from file, length: {len(transcript)} characters")
        except Exception as e:
            logger.error(f"Failed to read transcript file: {transcript_input}")
            logger.exception("Full exception details for file reading error:")
            raise
    else:
        transcript = transcript_input
        logger.debug(f"Input treated as direct text, length: {len(transcript)} characters")
    
    logger.debug(f"Final transcript preview: {repr(transcript[:200])}...")

    # 1. Chunking
    logger.info("Step 1: Starting transcript chunking")
    logger.debug(f"Configured chunk size: {config.CHUNK_SIZE}")
    chunker = ChunkingService()
    chunks = chunker.transcript_to_chunks(
        transcript,
        chunk_size=config.CHUNK_SIZE
    )
    logger.info(f"Step 1 completed: Chunked transcript into {len(chunks)} chunks")
    logger.debug(f"Chunks preview: {repr([c.get('id', 'unknown') for c in chunks[:5]])}...")
    if debug:
        print(f"Chunked {len(chunks)} utterances.")

    # 2. Clustering
    logger.info("Step 2: Starting chunk clustering")
    logger.debug(f"Configured model type: {config.MODEL_TYPE}")
    factory = AIModelFactory()
    logger.debug("Creating AI model instance")
    model = factory.create_model(
        model_type=config.MODEL_TYPE,
        config=config.get_model_config()
    )
    logger.debug("AI model created successfully")
    
    clustering_service = ClusteringService()
    logger.debug("Starting chunks to segments clustering")
    clustered_segments = clustering_service.chunks_to_segments(chunks, model)
    logger.info(f"Step 2 completed: Clustered into {len(clustered_segments)} segments")
    logger.debug(f"Clustered segments preview: {repr([s.get('segment_id', 'unknown') for s in clustered_segments[:5]])}...")
    if debug:
        print(f"Clustered into {len(clustered_segments)} segments.")

    # 3. Filtering for actionable segments
    logger.info("Step 3: Starting actionable segments filtering")
    filtering_service = FilteringService()
    logger.debug("Filtering segments for actionable content")
    actionable_segments = filtering_service.filter_for_actionable_segments(clustered_segments, model)
    logger.info(f"Step 3 completed: Found {len(actionable_segments)} actionable segments out of {len(clustered_segments)} total")
    logger.debug(f"Actionable segments: {repr([s.get('segment_id', 'unknown') for s in actionable_segments])}")
    if debug:
        print(f"Found {len(actionable_segments)} actionable segments.")

    # 4. Extraction of structured action info
    logger.info("Step 4: Starting structured action extraction")
    extraction_service = ExtractionService()
    logger.debug("Extracting structured action summary from actionable segments")
    summary = extraction_service.get_structured_action_summary(actionable_segments, model, debug=debug)
    logger.info(f"Step 4 completed: Extracted {summary.get('total_actions', 0)} actions from {summary.get('total_segments_processed', 0)} segments")
    logger.debug(f"Final summary structure: total_segments_processed={summary.get('total_segments_processed', 0)}, total_actions={summary.get('total_actions', 0)}, actions_count={len(summary.get('actions', []))}")

    logger.info("Action extraction pipeline completed successfully")
    logger.debug("Returning structured action summary")
    return summary
