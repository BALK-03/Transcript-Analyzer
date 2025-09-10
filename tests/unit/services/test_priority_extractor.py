import pytest
from src.services.extraction.priority_extractor import PriorityExtractor
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
    mocker.patch("config.paths.EXTRACTION_PRIORITY_PROMPT", new="dummy_prompt_path")

@pytest.fixture
def extractor():
    return PriorityExtractor()

class TestPriorityExtractor:

    def test_health_check_is_ok(self, extractor):
        assert extractor
        assert extractor.prompt_filepath == "dummy_prompt_path"
        assert len(extractor.valid_priorities) == 3

    def test_init(self, extractor):
        assert extractor.prompt_filepath == "dummy_prompt_path"
        assert extractor.valid_priorities == ["High", "Medium", "Low"]

    def test_extract_returns_correct_data_on_success(self, mocker, extractor):
        # Arrange
        segment = {"id": "123"}
        model = MockAIModel()
        mock_prep_prompt = mocker.patch.object(extractor, "_prep_prompt")
        mock_json_response = {"priority": "High", "confidence": 90, "reasoning": "Test reason"}
        mocker.patch.object(extractor, "_extract_json_from_text", return_value=mock_json_response)
        mocker.patch.object(model, "process", return_value=json.dumps(mock_json_response))

        # Act
        result = extractor.extract(segment, model)

        # Assert
        mock_prep_prompt.assert_called_once_with(segment, None)
        assert result == mock_json_response

    def test_extract_defaults_to_medium_for_invalid_priority(self, mocker, extractor):
        # Arrange
        segment = {"id": "123"}
        model = MockAIModel()
        mock_json_response = {"priority": "Critical"}
        mocker.patch.object(extractor, "_extract_json_from_text", return_value=mock_json_response)
        
        # Act
        result = extractor.extract(segment, model)

        # Assert
        assert result["priority"] == "Medium"

    def test_extract_defaults_to_medium_if_priority_key_is_missing(self, mocker, extractor):
        # Arrange
        segment = {"id": "123"}
        model = MockAIModel()
        mock_json_response = {"confidence": 90}
        mocker.patch.object(extractor, "_extract_json_from_text", return_value=mock_json_response)
        
        # Act
        result = extractor.extract(segment, model)

        # Assert
        assert result["priority"] == "Medium"
        
    def test_extract_defaults_confidence_on_missing_or_invalid_key(self, mocker, extractor):
        # Arrange
        segment = {"id": "123"}
        model = MockAIModel()
        mock_json_response_missing = {"priority": "High"}
        mock_json_response_invalid = {"priority": "High", "confidence": "high"}
        
        mocker.patch.object(extractor, "_extract_json_from_text", return_value=mock_json_response_missing)
        result_missing = extractor.extract(segment, model)
        
        mocker.patch.object(extractor, "_extract_json_from_text", return_value=mock_json_response_invalid)
        result_invalid = extractor.extract(segment, model)
        
        # Assert
        assert result_missing["confidence"] == 50
        assert result_invalid["confidence"] == 50

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
        assert defaults == {"priority": "Medium", "confidence": 50, "reasoning": "Default due to extraction failure"}