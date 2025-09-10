import pytest
from src.services.extraction.category_extractor import CategoryExtractor
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
    mocker.patch("config.paths.EXTRACTION_CATEGORY_PROMPT", new="dummy_prompt_path")

@pytest.fixture
def extractor():
    return CategoryExtractor()

class TestCategoryExtractor:

    def test_health_check_is_ok(self, extractor):
        assert extractor
        assert extractor.prompt_filepath == "dummy_prompt_path"
        assert len(extractor.valid_categories) == 6

    def test_init(self, extractor):
        assert extractor.prompt_filepath == "dummy_prompt_path"
        assert extractor.valid_categories == ["Bug Fix", "Feature Development", "Research", "Documentation", "Meeting", "Other"]

    def test_extract_returns_correct_data_on_success(self, mocker, extractor):
        # Arrange
        segment = {"id": "123"}
        model = MockAIModel()
        mock_prep_prompt = mocker.patch.object(extractor, "_prep_prompt")
        mock_json_response = {"category": "Feature Development", "confidence": 90, "reasoning": "Test reason"}
        mocker.patch.object(extractor, "_extract_json_from_text", return_value=mock_json_response)
        mocker.patch.object(model, "process", return_value=json.dumps(mock_json_response))

        # Act
        result = extractor.extract(segment, model)

        # Assert
        mock_prep_prompt.assert_called_once_with(segment, None)
        assert result == mock_json_response

    def test_extract_defaults_to_other_for_invalid_category(self, mocker, extractor):
        # Arrange
        segment = {"id": "123"}
        model = MockAIModel()
        mock_json_response = {"category": "Invalid Category"}
        mocker.patch.object(extractor, "_extract_json_from_text", return_value=mock_json_response)
        
        # Act
        result = extractor.extract(segment, model)

        # Assert
        assert result["category"] == "Other"

    def test_extract_defaults_to_other_if_category_key_is_missing(self, mocker, extractor):
        # Arrange
        segment = {"id": "123"}
        model = MockAIModel()
        mock_json_response = {"confidence": 90}
        mocker.patch.object(extractor, "_extract_json_from_text", return_value=mock_json_response)
        
        # Act
        result = extractor.extract(segment, model)

        # Assert
        assert result["category"] == "Other"
        
    def test_extract_defaults_confidence_on_missing_or_invalid_key(self, mocker, extractor):
        # Arrange
        segment = {"id": "123"}
        model = MockAIModel()
        mock_json_response_missing = {"category": "Bug Fix"}
        mock_json_response_invalid = {"category": "Bug Fix", "confidence": "high"}
        
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
        assert defaults == {"category": "Other", "confidence": 50, "reasoning": "Default due to extraction failure"}