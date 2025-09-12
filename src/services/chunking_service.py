import re
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ChunkingService:
    def __init__(self):
        logger.debug("Initializing ChunkingService")
        # A simple pattern to split text into sentences
        # based on common punctuation followed by a space or end of string
        self._sentence_split_pattern = r"(?<=[.!?])\s+"
        logger.debug(f"Sentence split pattern configured: {repr(self._sentence_split_pattern)}")
        logger.info("ChunkingService successfully initialized")

    def transcript_to_chunks(self, raw_text: str, chunk_size: int = 3) -> list[dict]:
        """
        Parse a transcript into structured chunks by sentences.

        Args:
            raw_text (str): The raw transcript text.
            chunk_size (int): The number of sentences per chunk. Defaults to 3.

        Returns:
            list of dict: Each dict includes 'id', 'order', and 'content'.
        """
        logger.info("Starting transcript to chunks conversion")
        logger.debug(f"Raw text length: {len(raw_text) if raw_text else 0} characters")
        logger.debug(f"Chunk size parameter: {chunk_size}")
        logger.debug(f"Raw text preview: {repr(raw_text[:200]) if raw_text else 'None'}...")
        
        if not (raw_text and isinstance(raw_text, str)):
            logger.error("Invalid input: text must be a non-empty string")
            raise ValueError("Input text must be a non-empty string.")

        logger.debug("Splitting raw text into sentences using regex pattern")
        sentences = re.split(self._sentence_split_pattern, raw_text.strip())
        logger.debug(f"Successfully split text into {len(sentences)} sentences")
        logger.debug(f"First few sentences: {repr(sentences[:3]) if sentences else 'None'}")
        
        chunks = []
        chunk_id = 0
        logger.debug("Starting chunk creation process")

        for i in range(0, len(sentences), chunk_size):
            logger.debug(f"Processing sentences {i} to {i + chunk_size - 1}")
            chunk_sentences = sentences[i:i + chunk_size]
            logger.debug(f"Chunk sentences count: {len(chunk_sentences)}")
            
            chunk_content = " ".join(s.strip() for s in chunk_sentences if s.strip())
            logger.debug(f"Chunk content length: {len(chunk_content)} characters")

            if chunk_content:
                logger.debug(f"Creating chunk with id {chunk_id}")
                chunk = {
                    "id": chunk_id,
                    "order": chunk_id,
                    "content": chunk_content
                }
                chunks.append(chunk)
                logger.debug(f"Chunk {chunk_id} created successfully with content: {repr(chunk_content[:100])}...")
                chunk_id += 1
            else:
                logger.debug(f"Skipping empty chunk at position {i}")
        
        logger.info(f"Transcript to chunks conversion completed successfully. Created {len(chunks)} chunks")
        logger.debug(f"Total chunks created: {len(chunks)}")
        return chunks
    


# class ChunkingService:
#     def __init__(self):
#         self._pattern = r"\[\d{1,2}:\d{2} (?:AM|PM)\] ([^:]+):"
        
#     def transcript_to_chunks(self, raw_text: str, start_marker=None, end_marker=None) -> list[dict]:
#         """
#         Parse a transcript into structured chunks with metadata.
        
#         Args:
#             raw_text (str): The raw transcript text
#             start_marker (str, optional): Marker to indicate where parsing should start
#             end_marker (str, optional): Marker to indicate where parsing should end
            
#         Returns:
#             list of dict: Each dict includes 'id', 'order', and 'context'
#         """
#         if not (raw_text and isinstance(raw_text, str)):
#             raise ValueError("Input text must be a non empty string.")

#         if start_marker:
#             if not isinstance(start_marker, str):
#                 raise ValueError("Start marker must be a string.")
#             start_idx = raw_text.find(start_marker)
#             if start_idx == -1:
#                 raise ValueError(f"Start marker '{start_marker}' not found.")
#             raw_text = raw_text[start_idx + len(start_marker):]
        
#         if end_marker:
#             if not isinstance(end_marker, str):
#                 raise ValueError("End marker must be a string.")
#             end_idx = raw_text.find(end_marker)
#             if end_idx == -1:
#                 raise ValueError(f"End marker '{end_marker}' not found.")
#             raw_text = raw_text[:end_idx]
        
#         matches = list(re.finditer(self._pattern, raw_text))
#         chunks = []

#         for i, match in enumerate(matches):
#             start = match.end()
#             end = matches[i + 1].start() if i + 1 < len(matches) else len(raw_text)
#             speaker = match.group(1).strip()
#             utterance = raw_text[start:end].strip().replace('\n', ' ')
#             chunk_text = f"{speaker}: {utterance}"

#             chunk = {
#                 "id": i,
#                 "order": i,
#                 "content": chunk_text
#             }
#             chunks.append(chunk)
        
#         return chunks
