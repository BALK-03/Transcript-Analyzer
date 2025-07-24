import os
from pathlib import Path

class Config:
    """Configuration class for the pipeline."""
    
    # File handling
    MAX_FILENAME_LENGTH = 255
    DEFAULT_TRANSCRIPT_FILE = 'data/transcript.txt'
    
    # Chunking service
    CHUNK_START_MARKER = "TRANSCRIPT:"
    CHUNK_END_MARKER = "[END TRANSCRIPT"
    
    # AI Model configuration
    MODEL_TYPE = "gemini"
    MODEL_NAME = "gemini-2.0-flash"
    API_KEY_ENV_VAR = "GEMINI_API_KEY"
    
    # Retry configuration
    MAX_RETRIES = 5
    BASE_DELAY = 1.0
    MAX_DELAY = 8.0
    
    # Pipeline settings
    DEBUG_MODE = False
    
    @classmethod
    def get_model_config(cls) -> dict:
        """Get the model configuration dictionary."""
        return {
            "api_key": os.getenv(cls.API_KEY_ENV_VAR),
            "model": cls.MODEL_NAME,
            "max_retries": cls.MAX_RETRIES,
            "base_delay": cls.BASE_DELAY,
            "max_delay": cls.MAX_DELAY
        }
    
    @classmethod
    def is_valid_file_path(cls, input_string: str) -> bool:
        """Check if input string is a valid file path based on heuristics."""
        return (
            len(input_string) <= cls.MAX_FILENAME_LENGTH and
            '\n' not in input_string and
            input_string.lower().endswith('.txt') and
            Path(input_string).is_file()
        )

class DevelopmentConfig(Config):
    """Development environment configuration."""
    DEBUG_MODE = True
    MAX_RETRIES = 3


def get_config():
    """Get configuration based on environment variable."""
    return DevelopmentConfig()