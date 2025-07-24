#!/bin/bash

set -e

CONFIG_DIR="config"
ENV_FILE="$CONFIG_DIR/.env"
MODELS=("gemini" "openai")

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

mkdir -p "$CONFIG_DIR"

if [[ "$model" == "gemini" ]]; then
    cat > "$ENV_FILE" <<EOF
GEMINI_API_KEY=$api_key
EOF
elif [[ "$model" == "openai" ]]; then
    cat > "$ENV_FILE" <<EOF
OPENAI_API_KEY=$api_key
EOF
fi

echo "Created .env file at $ENV_FILE"

if ! command -v uv &> /dev/null; then
    echo "🔧 Downloading uv for Linux users (skip if you have it)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
else
    echo "uv is already installed."
fi

echo "Creating virtual environment with uv..."
uv venv .venv
source .venv/bin/activate

echo -n "Installing dependencies from pyproject.toml..."

# Run in background and show spinner
(uv sync > logs/install.log 2>&1) &
pid=$!

spinner="/-\|"
while kill -0 $pid 2>/dev/null; do
    for i in $spinner; do
        echo -ne "\rInstalling dependencies from pyproject.toml... $i"
        sleep 0.1
    done
done

echo -e "\rDependencies installed!

echo "Starting FastAPI server (main.py)..."
mkdir -p logs
nohup python3 main.py > logs/fastapi.log 2>&1 &

echo "Starting Gradio UI (gradio_ui.py)..."
python3 gradio_ui.py &

sleep 3

echo ""
echo "Application is running!"
echo "Visit the Gradio UI at: http://127.0.0.1:7861"
