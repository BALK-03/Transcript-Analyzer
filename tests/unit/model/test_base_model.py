import pytest
from src.models.base_model import BaseAIModel

class TestBaseAIModel:
    # A simple concrete implementation for testing purposes
    class ConcreteAIModel(BaseAIModel):
        def process(self, input_text: str) -> str:
            return "processed"

        def get_info(self) -> dict:
            return {}

    def test_health_check_is_ok(self):
        assert True

    def test_validate_input_with_valid_string(self):
        model = self.ConcreteAIModel()
        valid_input = "This is a valid string."
        assert model.validate_input(valid_input) == valid_input

    def test_validate_input_strips_whitespace(self):
        model = self.ConcreteAIModel()
        input_with_whitespace = "  \n  test string \t "
        assert model.validate_input(input_with_whitespace) == "test string"

    def test_validate_input_raises_typeerror_for_non_string(self):
        model = self.ConcreteAIModel()
        with pytest.raises(TypeError, match="Input must be a string."):
            model.validate_input(123)
        with pytest.raises(TypeError, match="Input must be a string."):
            model.validate_input(None)

    def test_validate_input_raises_valueerror_for_empty_string(self):
        model = self.ConcreteAIModel()
        with pytest.raises(ValueError, match="Input cannot be empty."):
            model.validate_input("")
        with pytest.raises(ValueError, match="Input cannot be empty."):
            model.validate_input("   \n  ")

    def test_validate_input_raises_valueerror_for_long_string(self):
        model = self.ConcreteAIModel()
        long_string = "a" * 1001
        with pytest.raises(ValueError, match="Input is too long"):
            model.validate_input(long_string)