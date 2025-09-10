import pytest
from src.models.base_model import BaseAIModel
from src.models.model_factory import AIModelFactory

class TestAIModelFactory:
    # A mock model for factory testing
    class MockModel(BaseAIModel):
        def __init__(self, config=None):
            super().__init__(config)

        def process(self, input_text: str) -> str:
            return "mocked"

        def get_info(self) -> dict:
            return {}

    def test_health_check_is_ok(self):
        assert True

    def test_register_model_registers_correctly(self):
        initial_count = len(AIModelFactory._models)
        AIModelFactory.register_model("mock", self.MockModel)
        assert len(AIModelFactory._models) == initial_count + 1
        assert AIModelFactory._models["mock"] == self.MockModel

    def test_register_model_raises_typeerror_for_invalid_class(self):
        class InvalidClass:
            pass
        with pytest.raises(TypeError, match="Registered class must be a subclass of BaseAIModel."):
            AIModelFactory.register_model("invalid", InvalidClass)

    def test_create_model_creates_correct_instance(self):
        AIModelFactory.register_model("mock", self.MockModel)
        model = AIModelFactory.create_model("mock")
        assert isinstance(model, self.MockModel)
        assert isinstance(model, BaseAIModel)

    def test_create_model_raises_valueerror_for_unknown_type(self):
        # We assume the factory might have other models registered from previous tests
        AIModelFactory._models.clear()
        with pytest.raises(ValueError, match="Unknown model type"):
            AIModelFactory.create_model("unknown")

    def test_get_available_models_returns_correct_list(self):
        # Ensure the test is isolated by clearing the factory state
        AIModelFactory._models.clear()
        AIModelFactory.register_model("mock1", self.MockModel)
        AIModelFactory.register_model("mock2", self.MockModel)
        available = AIModelFactory.get_available_models()
        assert "mock1" in available
        assert "mock2" in available
        assert len(available) == 2