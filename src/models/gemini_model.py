from typing import Any
import os, time, random
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, InternalServerError, ServiceUnavailable
from src.models.base_model import BaseAIModel
from src.models.model_factory import AIModelFactory
from src.utils.logger import get_logger

logger = get_logger(__name__)


class GeminiAIModel(BaseAIModel):
    def __init__(self, config: dict[str, Any] = None):
        logger.debug("Initializing GeminiAIModel")
        super().__init__(config)
        
        logger.debug("Extracting configuration parameters")
        self.api_key = self.config.get("api_key") or os.getenv("GEMINI_API_KEY")
        self.model_name = self.config.get("model", "gemini-2.0-flash")
        self.max_retries = self.config.get("max_retries", 5)
        self.base_delay = self.config.get("base_delay", 1.0)
        self.max_delay = self.config.get("max_delay", 10.0)
        
        logger.debug(f"Configuration extracted - model: {self.model_name}, max_retries: {self.max_retries}, base_delay: {self.base_delay}, max_delay: {self.max_delay}")
        logger.debug(f"API key present: {bool(self.api_key)}")

        logger.debug("Validating configuration parameters")
        if not self.api_key or not isinstance(self.api_key, str):
            logger.error("Missing or invalid API key")
            raise ValueError("Missing or invalid API key.")
        if not isinstance(self.model_name, str):
            logger.error(f"Invalid model name type: {type(self.model_name)}")
            raise TypeError("Model name must be a string.")
        # <= 0 instead of < 0 to force retries, for a more robust api handling
        if not isinstance(self.max_retries, int) or self.max_retries <= 0:
            logger.error(f"Invalid max_retries value: {self.max_retries}")
            raise ValueError("max_retries must be a positive integer.")
        if not (isinstance(self.base_delay, (int, float)) and self.base_delay > 0):
            logger.error(f"Invalid base_delay value: {self.base_delay}")
            raise ValueError("base_delay must be a non-negative number.")
        if not (isinstance(self.max_delay, (int, float)) and self.max_delay > self.base_delay):
            logger.error(f"Invalid max_delay value: {self.max_delay} (base_delay: {self.base_delay})")
            raise ValueError("max_delay must be greater than base_delay.")
        
        logger.debug("Configuration validation completed successfully")
        logger.debug("Configuring Google Generative AI client")
        genai.configure(api_key=self.api_key)
        logger.debug(f"Creating GenerativeModel instance with model: {self.model_name}")
        self.model = genai.GenerativeModel(self.model_name)
        logger.info("GeminiAIModel successfully initialized and configured")

    def _exponential_backoff(self, attempt: int) -> float:
        logger.debug(f"Calculating exponential backoff for attempt {attempt}")
        delay = min(self.base_delay * (2 ** attempt), self.max_delay)
        jitter = random.uniform(0, delay)
        logger.debug(f"Backoff calculated - base delay: {delay:.2f}s, with jitter: {jitter:.2f}s")
        return jitter
    
    def _call_model(self, input_text: str) -> str:
        logger.debug("Making API call to Gemini model")
        logger.debug(f"Input text length: {len(input_text)} characters")
        logger.debug(f"Input text preview: {repr(input_text[:100])}...")
        
        try:
            response = self.model.generate_content(input_text)
            logger.debug("Successfully received response from Gemini API")
            response_text = response.text.strip()
            logger.debug(f"Response length: {len(response_text)} characters")
            logger.debug(f"Response preview: {repr(response_text[:100])}...")
            return response_text
        except Exception as e:
            logger.error(f"Error occurred during Gemini API call: {str(e)}")
            logger.exception("Full exception details for Gemini API call error:")
            raise Exception(" Problem occured while generating content.") from e
    
    def process(self, input_text):
        logger.info("Starting Gemini model processing with retry mechanism")
        logger.debug(f"Input text length: {len(input_text)} characters")
        logger.debug(f"Max retries configured: {self.max_retries}")
        
        for attempt in range(self.max_retries):
            logger.debug(f"Processing attempt {attempt + 1} of {self.max_retries}")
            try:
                result = self._call_model(input_text)
                logger.info(f"Gemini model processing successful on attempt {attempt + 1}")
                return result
            except (ResourceExhausted, InternalServerError, ServiceUnavailable) as e:
                logger.warning(f"Transient error on attempt {attempt + 1}: {str(e)}")
                delay = self._exponential_backoff(attempt)
                logger.info(f"Retrying in {delay:.2f}s... (attempt {attempt + 1} of {self.max_retries})")
                print(f"[Retry {attempt+1}] Transient error: {e}. Retrying in {delay:.2f}s...")
                time.sleep(delay)
            except Exception as e:
                logger.error(f"Fatal error on attempt {attempt + 1}: {str(e)}")
                logger.exception("Full exception details for fatal Gemini processing error:")
                print(f" Fatal error: {e}")
                break
        
        logger.error(f"Gemini API failed after {self.max_retries} retries")
        raise RuntimeError("Gemini API failed after max retries.")
    
    def get_info(self):
        logger.debug("Returning model information")
        info = {
            "provider": "Google",
            "model": self.model_name,
            "description": "Gemini model via Google Generative AI API"
        }
        logger.debug(f"Model info: {repr(info)}")
        return info


# Dynamic Registration for this class to follow the Open-Closed Principle
logger.debug("Registering GeminiAIModel with factory")
AIModelFactory.register_model("gemini", GeminiAIModel)
logger.debug("GeminiAIModel successfully registered with factory")