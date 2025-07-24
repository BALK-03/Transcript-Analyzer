import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, InternalServerError, ServiceUnavailable
import random
import time
from typing import Any
import os, sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.models.base_model import BaseAIModel


# TODO:
#   - For default config values, use config files, for better code changing later
class GeminiAIModel(BaseAIModel):
    def __init__(self, config: dict[str, Any] = None):
        super().__init__(config)
        self.api_key = self.config.get("api_key") or os.getenv("GEMINI_API_KEY")
        self.model_name = self.config.get("model", "gemini-2.0-flash")
        self.max_retries = self.config.get("max_retries", 5)
        self.base_delay = self.config.get("base_delay", 1.0)
        self.max_delay = self.config.get("max_delay", 10.0)

        if not self.api_key or not isinstance(self.api_key, str):
            raise ValueError("Missing or invalid API key.")
        if not isinstance(self.model_name, str):
            raise TypeError("Model name must be a string.")
        # <= 0 instead of < 0 to force retries, for a more robust api handling
        if not isinstance(self.max_retries, int) or self.max_retries <= 0:
            raise ValueError("max_retries must be a positive integer.")
        if not (isinstance(self.base_delay, (int, float)) and self.base_delay > 0):
            raise ValueError("base_delay must be a non-negative number.")
        if not (isinstance(self.max_delay, (int, float)) and self.max_delay > self.base_delay):
            raise ValueError("max_delay must be greater than base_delay.")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)

    def _exponential_backoff(self, attempt: int) -> float:
        delay = min(self.base_delay * (2 ** attempt), self.max_delay)
        jitter = random.uniform(0, delay)
        return jitter
    
    def _call_model(self, input_text: str) -> str:
        response = self.model.generate_content(input_text)
        return response.text.strip()
    
    def process(self, input_text):
        for attempt in range(self.max_retries):
            try:
                return self._call_model(input_text)
            except (ResourceExhausted, InternalServerError, ServiceUnavailable) as e:
                delay = self._exponential_backoff(attempt)
                print(f"[GeminiModel][Retry {attempt+1}] Transient error: {e}. Retrying in {delay:.2f}s...")
                time.sleep(delay)
            except Exception as e:
                print(f"[GeminiModel] Fatal error: {e}")
                break
        raise RuntimeError("Gemini API failed after max retries.")
    
    def get_info(self):
        return {
            "provider": "Google",
            "model": self.model_name,
            "description": "Gemini model via Google Generative AI API"
        }
    

if __name__ == "__main__":
    import os, sys
    from dotenv import load_dotenv

    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    import paths

    load_dotenv(paths.ENV_FILE)

    # Example config (replace with your actual API key or set GEMINI_API_KEY in env)
    config = {
        "api_key": os.getenv("GEMINI_API_KEY"),
        "model": "gemini-2.0-flash",
        "max_retries": 5,
        "base_delay": 1.0,
        "max_delay": 8.0
    }

    # Instantiate the model
    model = GeminiAIModel(config)


    prompt = "Explain Machine Learning in 10 words."

    print(f"Prompt:\n{prompt}\n{'-' * 40}")

    try:
        output = model.process(prompt)
        print("Response:\n", output)
    except Exception as e:
        print("Failed to get response:", e)
