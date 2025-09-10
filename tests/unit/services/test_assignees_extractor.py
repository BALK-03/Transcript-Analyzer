import pytest
from src.services.extraction.assignee_extractor import AssigneesExtractor
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
    mocker.patch("config.paths.EXTRACTION_ASSIGNEES_PROMPT", new="dummy_prompt_path")

@pytest.fixture
def extractor():
    return AssigneesExtractor()

class TestAssigneesExtractor:

    def test_health_check_is_ok(self, extractor):
        assert extractor
        assert extractor.prompt_filepath == "dummy_prompt_path"

    def test_init(self, extractor):
        assert extractor.prompt_filepath == "dummy_prompt_path"

    def test_extract_returns_correct_data_on_success(self, mocker, extractor):
        # Arrange
        segment = {"id": "123", "text": "assign to John"}
        model = MockAIModel()
        mock_prep_prompt = mocker.patch.object(extractor, "_prep_prompt", return_value="dummy_prompt")
        mock_json_response = {"assignees": ["John", "Jane"]}
        mock_extract_json = mocker.patch.object(extractor, "_extract_json_from_text", return_value=mock_json_response)
        mocker.patch.object(model, "process", return_value=json.dumps(mock_json_response))

        # Act
        result = extractor.extract(segment, model)

        # Assert
        mock_prep_prompt.assert_called_once_with(segment)
        assert result == mock_json_response

    def test_extract_returns_defaults_on_json_extraction_failure(self, mocker, extractor):
        # Arrange
        segment = {"id": "123", "text": "assign to John"}
        model = MockAIModel()
        mocker.patch.object(extractor, "_prep_prompt")
        mocker.patch.object(extractor, "_extract_json_from_text", return_value=None)
        
        # Act
        result = extractor.extract(segment, model)

        # Assert
        assert result == extractor.get_default_values()

    def test_extract_returns_defaults_when_assignees_key_is_missing(self, mocker, extractor):
        # Arrange
        segment = {"id": "123", "text": "assign to John"}
        model = MockAIModel()
        mocker.patch.object(extractor, "_prep_prompt")
        mock_json_response = {"other_key": "value"} # missing 'assignees'
        mocker.patch.object(extractor, "_extract_json_from_text", return_value=mock_json_response)
        
        # Act
        result = extractor.extract(segment, model)

        # Assert
        assert result == extractor.get_default_values()

    def test_extract_returns_defaults_on_exception(self, mocker, extractor):
        # Arrange
        segment = {"id": "123", "text": "assign to John"}
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
        assert defaults == {"assignees": []}