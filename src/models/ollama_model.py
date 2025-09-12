import os
import time
import random
import requests
from typing import Any
from requests.exceptions import ConnectionError, HTTPError, Timeout

from src.models.base_model import BaseAIModel
from src.models.model_factory import AIModelFactory
from src.utils.logger import get_logger

logger = get_logger(__name__)


class OllamaAIModel(BaseAIModel):
    """
    A class to interact with a local or remote Ollama server.

    This model handles API calls, response parsing, and implements
    exponential backoff with retries to handle transient network or
    server issues. It is designed to be a drop-in replacement for
    other AI models in the factory pattern.
    """
    def __init__(self, config: dict[str, Any] = None):
        """
        Initializes the OllamaAIModel with configuration settings.

        Args:
            config (dict[str, Any], optional): A dictionary containing configuration
                parameters. Defaults to None.
        """
        logger.debug("Initializing OllamaAIModel")
        super().__init__(config)
        
        logger.debug("Extracting configuration parameters")
        self.base_url = self.config.get("base_url") or os.getenv("OLLAMA_API_BASE_URL", "http://localhost:11434")
        self.model_name = self.config.get("model", "llama3")
        self.max_retries = self.config.get("max_retries", 5)
        self.base_delay = self.config.get("base_delay", 1.0)
        self.max_delay = self.config.get("max_delay", 10.0)

        logger.debug(f"Configuration extracted - base_url: {self.base_url}, model: {self.model_name}, max_retries: {self.max_retries}, base_delay: {self.base_delay}, max_delay: {self.max_delay}")

        # Parameter validation
        logger.debug("Validating configuration parameters")
        if not isinstance(self.base_url, str):
            logger.error(f"Invalid base URL type: {type(self.base_url)}")
            raise TypeError("Base URL must be a string.")
        if not isinstance(self.model_name, str):
            logger.error(f"Invalid model name type: {type(self.model_name)}")
            raise TypeError("Model name must be a string.")
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
        self.generate_url = f"{self.base_url}/api/generate"
        logger.debug(f"Generate URL configured: {self.generate_url}")
        logger.info("OllamaAIModel successfully initialized")

    def _exponential_backoff(self, attempt: int) -> float:
        """
        Calculates the exponential backoff delay with jitter.

        Args:
            attempt (int): The current retry attempt number.

        Returns:
            float: The calculated delay in seconds.
        """
        logger.debug(f"Calculating exponential backoff for attempt {attempt}")
        delay = min(self.base_delay * (2 ** attempt), self.max_delay)
        jitter = random.uniform(0, delay)
        logger.debug(f"Backoff calculated - base delay: {delay:.2f}s, with jitter: {jitter:.2f}s")
        return jitter
    
    def _call_model(self, input_text: str) -> str:
        """
        Makes a single API call to the Ollama server.

        Args:
            input_text (str): The text prompt to send to the model.

        Returns:
            str: The generated text response.
        
        Raises:
            requests.exceptions.RequestException: If the API call fails.
        """
        logger.debug("Making API call to Ollama server")
        logger.debug(f"Input text length: {len(input_text)} characters")
        logger.debug(f"Input text preview: {repr(input_text[:100])}...")
        
        payload = {
            "model": self.model_name,
            "prompt": input_text,
            "stream": False # We'll handle streaming in a separate method if needed.
        }
        logger.debug(f"API payload prepared: model={self.model_name}, stream=False")
        
        logger.debug(f"Sending POST request to: {self.generate_url}")
        response = requests.post(self.generate_url, json=payload, timeout=60)
        logger.debug(f"Received HTTP response with status code: {response.status_code}")
        
        response.raise_for_status()
        logger.debug("HTTP status check passed")
        
        data = response.json()
        logger.debug("Successfully parsed JSON response")
        logger.debug(f"Response data keys: {list(data.keys())}")
        
        generated_text = data.get("response", "").strip()
        logger.debug(f"Generated text length: {len(generated_text)} characters")
        logger.debug(f"Generated text preview: {repr(generated_text[:100])}...")
        
        if not generated_text:
            logger.error("Ollama API returned empty response")
            raise ValueError("Ollama API returned an empty response.")
        
        logger.debug("Ollama API call completed successfully")
        return generated_text
    
    def process(self, input_text: str) -> str:
        """
        Processes a given input text using the Ollama model with retries.

        Args:
            input_text (str): The text to process.

        Returns:
            str: The processed text from the model.
        
        Raises:
            RuntimeError: If the API call fails after the maximum number of retries.
        """
        logger.info("Starting Ollama model processing with retry mechanism")
        logger.debug(f"Input text length: {len(input_text)} characters")
        logger.debug(f"Max retries configured: {self.max_retries}")
        
        for attempt in range(self.max_retries):
            logger.debug(f"Processing attempt {attempt + 1} of {self.max_retries}")
            try:
                result = self._call_model(input_text)
                logger.info(f"Ollama model processing successful on attempt {attempt + 1}")
                return result
            except (ConnectionError, HTTPError, Timeout) as e:
                logger.warning(f"Transient error on attempt {attempt + 1}: {str(e)}")
                delay = self._exponential_backoff(attempt)
                logger.info(f"Retrying in {delay:.2f}s... (attempt {attempt + 1} of {self.max_retries})")
                print(f"[OllamaModel][Retry {attempt+1}] Transient error: {e}. Retrying in {delay:.2f}s...")
                time.sleep(delay)
            except Exception as e:
                logger.error(f"Fatal error on attempt {attempt + 1}: {str(e)}")
                logger.exception("Full exception details for fatal Ollama processing error:")
                print(f"[OllamaModel] Fatal error: {e}")
                break
        
        logger.error(f"Ollama API failed after {self.max_retries} retries")
        raise RuntimeError(f"Ollama API failed after {self.max_retries} retries.")
    
    def get_info(self) -> dict[str, Any]:
        """
        Returns information about the model.

        Returns:
            dict[str, Any]: A dictionary with provider, model, and description.
        """
        logger.debug("Returning model information")
        info = {
            "provider": "Ollama",
            "model": self.model_name,
            "description": f"Model served via a local Ollama server at {self.base_url}"
        }
        logger.debug(f"Model info: {repr(info)}")
        return info

# Dynamic Registration for this class
logger.debug("Registering OllamaAIModel with factory")
AIModelFactory.register_model("ollama", OllamaAIModel)
logger.debug("OllamaAIModel successfully registered with factory")
