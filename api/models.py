from pydantic import BaseModel
from typing import Any


class PipelineRequest(BaseModel):
    transcript: str  # raw text


class PipelineResponse(BaseModel):
    clustered_items: dict[str, Any]
