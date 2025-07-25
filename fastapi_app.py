from fastapi import FastAPI
from api.routes import pipeline
import uvicorn
from dotenv import load_dotenv
import paths

load_dotenv(paths.ENV_FILE)

app = FastAPI(
    title="Transcript Action Item Pipeline",
    version="1.0.0"
)

app.include_router(pipeline.router)


if __name__ == "__main__":
    uvicorn.run("fastapi_app:app", host="127.0.0.1", port=8000, reload=True)