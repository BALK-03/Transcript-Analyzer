#!/bin/bash

set -e

CONFIG_DIR="config"
ENV_FILE="$CONFIG_DIR/.env"

MODELS=("gemini"  "openai")

echo "Select the AI model you want to use:"
select model in "${MODELS[@]}"; do
    if [[ -n "$model" ]]; then
        echo "You selected: $model"
        break
    else
        echo "Invalid selection. Try again."
    fi
done

read -p "Enter your API key for $model: " api_key

if [$model -eq "gemini"]; then
cat > "$ENV_FILE" <<EOF
GEMINI_API_KEY=$api_key
EOF
elif [$model -eq "openai"]; then
cat > "$ENV_FILE" <<EOF
GEMINI_API_KEY=$api_key
EOF
fi

echo "Created .env file at $ENV_FILE"

echo "Downloading uv for linux users, if not a linux go to uv docs and download"
if [linux]; then
curl -LsSf https://astral.sh/uv/install.sh | sh
fi

echo "Creating virtual environment with uv..."
uv venv create --prompt myenv
source .venv/myenv/bin/activate

echo "Installing dependencies from pyproject.toml..."
uv sync

echo "Starting FastAPI server (main.py)..."
nohup python3 main.py > logs/fastapi.log 2>&1 &

echo "Starting Gradio UI (gradio_ui.py)..."
python3 gradio_ui.py &

sleep 3

echo ""
echo "Application should be running..."
echo "Gradio UI URL will be printed below when ready..."

echo "Open your browser and visit http://127.0.0.1:7860 to test the UI!"

wait
