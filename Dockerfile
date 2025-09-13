FROM python:3.11-slim

WORKDIR /app

COPY . .

# Using --no-cache-dir to keep the image size smaller
RUN pip install --no-cache-dir .

EXPOSE 8000

# The host is set to 0.0.0.0 to allow the container to accept connections from outside.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
