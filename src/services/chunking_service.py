import re

class ChunkingService:
    def __init__(self):
        # A simple pattern to split text into sentences
        # based on common punctuation followed by a space or end of string
        self._sentence_split_pattern = r"(?<=[.!?])\s+"

    def transcript_to_chunks(self, raw_text: str, chunk_size: int = 3) -> list[dict]:
        """
        Parse a transcript into structured chunks by sentences.

        Args:
            raw_text (str): The raw transcript text.
            chunk_size (int): The number of sentences per chunk. Defaults to 3.

        Returns:
            list of dict: Each dict includes 'id', 'order', and 'content'.
        """
        if not (raw_text and isinstance(raw_text, str)):
            raise ValueError("Input text must be a non-empty string.")

        sentences = re.split(self._sentence_split_pattern, raw_text.strip())
        
        chunks = []
        chunk_id = 0

        for i in range(0, len(sentences), chunk_size):
            chunk_sentences = sentences[i:i + chunk_size]
            
            chunk_content = " ".join(s.strip() for s in chunk_sentences if s.strip())

            if chunk_content:
                chunk = {
                    "id": chunk_id,
                    "order": chunk_id,
                    "content": chunk_content
                }
                chunks.append(chunk)
                chunk_id += 1
        
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
