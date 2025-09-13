from fastapi import FastAPI
from api.routes import pipeline
import uvicorn

app = FastAPI(
    title="Transcript Action Item Pipeline",
    version="1.0.0"
)

app.include_router(pipeline.router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)