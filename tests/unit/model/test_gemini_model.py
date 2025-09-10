import pytest
import os
import time
from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable
from src.models.gemini_model import GeminiAIModel
import google.generativeai as genai

class TestGeminiAIModel:
    # Mocking the genai library to prevent actual API calls
    @pytest.fixture(autouse=True)
    def mock_genai(self, mocker):
        mocker.patch("google.generativeai.configure")
        mocker.patch("google.generativeai.GenerativeModel")

    def test_health_check_is_ok(self, mocker):
        mocker.patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key"})
        assert GeminiAIModel()

    def test_constructor_with_valid_config(self, mocker):
        mocker.patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key"})
        model = GeminiAIModel(config={"model": "gemini-pro", "max_retries": 10, "base_delay": 2.0, "max_delay": 20.0})
        assert model.model_name == "gemini-pro"
        assert model.max_retries == 10

    def test_constructor_raises_valueerror_for_missing_api_key(self, mocker):
        mocker.patch.dict(os.environ, clear=True)
        with pytest.raises(ValueError, match="Missing or invalid API key."):
            GeminiAIModel()

    def test_constructor_raises_typeerror_for_invalid_model_name(self, mocker):
        mocker.patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key"})
        with pytest.raises(TypeError, match="Model name must be a string."):
            GeminiAIModel(config={"model": 123})

    def test_constructor_raises_valueerror_for_invalid_max_retries(self, mocker):
        mocker.patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key"})
        with pytest.raises(ValueError, match="max_retries must be a positive integer."):
            GeminiAIModel(config={"max_retries": 0})
        with pytest.raises(ValueError, match="max_retries must be a positive integer."):
            GeminiAIModel(config={"max_retries": -1})

    def test_constructor_raises_valueerror_for_invalid_base_delay(self, mocker):
        mocker.patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key"})
        with pytest.raises(ValueError, match="base_delay must be a non-negative number."):
            GeminiAIModel(config={"base_delay": 0})
        with pytest.raises(ValueError, match="base_delay must be a non-negative number."):
            GeminiAIModel(config={"base_delay": -1})

    def test_constructor_raises_valueerror_for_invalid_max_delay(self, mocker):
        mocker.patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key"})
        with pytest.raises(ValueError, match="max_delay must be greater than base_delay."):
            GeminiAIModel(config={"max_delay": 1.0, "base_delay": 1.0})

    def test_process_calls_model_and_returns_text(self, mocker):
        mocker.patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key"})
        model_instance = GeminiAIModel()
        mock_response = mocker.Mock()
        mock_response.text = "Mocked Response Text"
        mock_generate_content = mocker.patch.object(model_instance.model, 'generate_content', return_value=mock_response)
        
        result = model_instance.process("test input")

        mock_generate_content.assert_called_once_with("test input")
        assert result == "Mocked Response Text"

    def test_process_retries_on_transient_error(self, mocker):
        mocker.patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key"})
        model_instance = GeminiAIModel(config={"max_retries": 3})
        
        # Mock generate_content to raise an exception twice, then succeed
        mock_generate_content = mocker.patch.object(
            model_instance.model,
            'generate_content',
            # Pass a message string to each exception
            side_effect=[
                ServiceUnavailable("Service is temporarily unavailable."),
                ResourceExhausted("Quota limit reached."),
                mocker.Mock(text="Success")
            ]
        )
        mock_sleep = mocker.patch.object(time, 'sleep')
        
        result = model_instance.process("test input")

        assert mock_generate_content.call_count == 3
        assert mock_sleep.call_count == 2
        assert result == "Success"

    def test_process_raises_runtimeerror_after_max_retries(self, mocker):
        mocker.patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key"})
        model_instance = GeminiAIModel(config={"max_retries": 2})
        
        # Mock generate_content to always raise a transient exception
        mocker.patch.object(
            model_instance.model,
            'generate_content',
            # Pass a message string to each exception
            side_effect=[
                ServiceUnavailable("Service is unavailable."),
                ServiceUnavailable("Service is still unavailable."),
                ServiceUnavailable("Giving up now.")
            ]
        )
        
        with pytest.raises(RuntimeError, match="Gemini API failed after max retries."):
            model_instance.process("test input")

    def test_get_info_returns_correct_dict(self, mocker):
        mocker.patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key"})
        model = GeminiAIModel()
        info = model.get_info()
        assert info["provider"] == "Google"
        assert info["model"] == model.model_name
        assert "description" in info