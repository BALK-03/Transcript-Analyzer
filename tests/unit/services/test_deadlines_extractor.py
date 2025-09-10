import pytest
from src.services.extraction.deadlines_extractor import DeadlinesExtractor
from src.models.base_model import BaseAIModel
from config import paths
import json

# Dummy classes for mocking
class MockAIModel(BaseAIModel):
    def process(self, input_text: str) -> str:
        return "mocked_response"
    
    def get_info(self) -> dict:
        return {}

@pytest.fixture(autouse=True)
def mock_paths(mocker):
    mocker.patch("config.paths.EXTRACTION_DEADLINES_PROMPT", new="dummy_prompt_path")

@pytest.fixture
def extractor():
    return DeadlinesExtractor()

class TestDeadlinesExtractor:

    def test_health_check_is_ok(self, extractor):
        assert extractor
        assert extractor.prompt_filepath == "dummy_prompt_path"
        
    def test_init(self, extractor):
        assert extractor.prompt_filepath == "dummy_prompt_path"

    def test_extract_returns_correct_data_on_success(self, mocker, extractor):
        # Arrange
        segment = {"id": "123"}
        model = MockAIModel()
        mock_prep_prompt = mocker.patch.object(extractor, "_prep_prompt")
        mock_json_response = {"deadlines": ["2025-01-01"], "urgent_flags": ["review"]}
        mocker.patch.object(extractor, "_extract_json_from_text", return_value=mock_json_response)
        mocker.patch.object(model, "process", return_value=json.dumps(mock_json_response))
        
        # Act
        result = extractor.extract(segment, model)
        
        # Assert
        mock_prep_prompt.assert_called_once_with(segment, None)
        assert result == mock_json_response
        
    def test_extract_defaults_deadlines_on_missing_key(self, mocker, extractor):
        # Arrange
        segment = {"id": "123"}
        model = MockAIModel()
        mock_json_response = {"urgent_flags": ["review"]}
        mocker.patch.object(extractor, "_extract_json_from_text", return_value=mock_json_response)
        
        # Act
        result = extractor.extract(segment, model)
        
        # Assert
        assert result["deadlines"] == []

    def test_extract_defaults_urgent_flags_on_missing_key(self, mocker, extractor):
        # Arrange
        segment = {"id": "123"}
        model = MockAIModel()
        mock_json_response = {"deadlines": ["2025-01-01"]}
        mocker.patch.object(extractor, "_extract_json_from_text", return_value=mock_json_response)
        
        # Act
        result = extractor.extract(segment, model)
        
        # Assert
        assert result["urgent_flags"] == []
    
    def test_extract_returns_defaults_on_json_extraction_failure(self, mocker, extractor):
        # Arrange
        segment = {"id": "123"}
        model = MockAIModel()
        mocker.patch.object(extractor, "_extract_json_from_text", return_value=None)
        
        # Act
        result = extractor.extract(segment, model)
        
        # Assert
        assert result == extractor.get_default_values()

    def test_extract_returns_defaults_on_exception(self, mocker, extractor):
        # Arrange
        segment = {"id": "123"}
        model = MockAIModel()
        mocker.patch.object(extractor, "_prep_prompt", side_effect=Exception("Test error"))
        
        # Act
        result = extractor.extract(segment, model)
        
        # Assert
        assert result == extractor.get_default_values()

    def test_get_default_values(self, extractor):
        # Act
        defaults = extractor.get_default_values()
        
        # Assert
        assert defaults == {"deadlines": [], "urgent_flags": []}