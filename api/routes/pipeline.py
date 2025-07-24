import os, sys
from fastapi import APIRouter, HTTPException

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from api.models import PipelineRequest, PipelineResponse
from src.services.pipeline_service import run_pipeline

router = APIRouter()

@router.post("/pipeline", response_model=PipelineResponse)
def process_pipeline(request: PipelineRequest):
    try:
        results = run_pipeline(request.transcript)
        return {"clustered_items": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
