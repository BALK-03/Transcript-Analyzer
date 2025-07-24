import openai
from openai import OpenAIError, RateLimitError, APIError
import random
import time
from typing import Any
import os, sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.models.base_model import BaseAIModel


class OpenAIAIModel(BaseAIModel):
    def __init__(self, config: dict[str, Any] = None):
        super().__init__(config)
        self.api_key = self.config.get("api_key") or os.getenv("OPENAI_API_KEY")
        self.model_name = self.config.get("model", "gpt-4o")
        self.max_retries = self.config.get("max_retries", 5)
        self.base_delay = self.config.get("base_delay", 1.0)
        self.max_delay = self.config.get("max_delay", 10.0)

        if not self.api_key or not isinstance(self.api_key, str):
            raise ValueError("Missing or invalid API key.")
        if not isinstance(self.model_name, str):
            raise TypeError("Model name must be a string.")
        if not isinstance(self.max_retries, int) or self.max_retries <= 0:
            raise ValueError("max_retries must be a positive integer.")
        if not (isinstance(self.base_delay, (int, float)) and self.base_delay > 0):
            raise ValueError("base_delay must be a non-negative number.")
        if not (isinstance(self.max_delay, (int, float)) and self.max_delay > self.base_delay):
            raise ValueError("max_delay must be greater than base_delay.")

        openai.api_key = self.api_key

    def _exponential_backoff(self, attempt: int) -> float:
        delay = min(self.base_delay * (2 ** attempt), self.max_delay)
        jitter = random.uniform(0, delay)
        return jitter

    def _call_model(self, input_text: str) -> str:
        response = openai.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": input_text}],
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()

    def process(self, input_text: str) -> str:
        for attempt in range(self.max_retries):
            try:
                return self._call_model(input_text)
            except (RateLimitError, APIError, OpenAIError) as e:
                delay = self._exponential_backoff(attempt)
                print(f"[OpenAIModel][Retry {attempt+1}] Transient error: {e}. Retrying in {delay:.2f}s...")
                time.sleep(delay)
            except Exception as e:
                print(f"[OpenAIModel] Fatal error: {e}")
                break
        raise RuntimeError("OpenAI API failed after max retries.")

    def get_info(self):
        return {
            "provider": "OpenAI",
            "model": self.model_name,
            "description": "OpenAI model via Chat Completion API"
        }


if __name__ == "__main__":
    from dotenv import load_dotenv
    import paths

    load_dotenv(paths.ENV_FILE)

    config = {
        "api_key": os.getenv("OPENAI_API_KEY"),
        "model": "gpt-4o",
        "max_retries": 5,
        "base_delay": 1.0,
        "max_delay": 8.0,
    }

    model = OpenAIAIModel(config)

    prompt = "Explain Machine Learning in 10 words."

    print(f"Prompt:\n{prompt}\n{'-' * 40}")

    try:
        output = model.process(prompt)
        print("Response:\n", output)
    except Exception as e:
        print("Failed to get response:", e)
