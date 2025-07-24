from pathlib import Path

# Base project directory
BASE_DIR = Path(__file__).resolve().parent

# .env file
ENV_FILE = BASE_DIR / "config" / ".env"

# Prompts directory
CLUSTERING_SERVICE_PROMPT = BASE_DIR / "src"/ "prompts" / "clustering_service_prompt.txt"
FILTERING_SERVICE_PROMPT = BASE_DIR / "src" / "prompts" / "filtering_service_prompt.txt"
EXTRACTION_ASSIGNEES_PROMPT = BASE_DIR / "src"/ "prompts" / "extraction_assignees_prompt.txt"
EXTRACTION_DEADLINES_PROMPT = BASE_DIR / "src"/ "prompts" / "extraction_deadlines_prompt.txt"
EXTRACTION_PRIORITY_PROMPT = BASE_DIR / "src"/ "prompts" / "extraction_priority_prompt.txt"
EXTRACTION_CATEGORY_PROMPT = BASE_DIR / "src"/ "prompts" / "extraction_category_prompt.txt"