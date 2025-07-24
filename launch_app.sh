#!/bin/bash

set -e  # Exit immediately on error

CONFIG_DIR="config"
ENV_FILE="$CONFIG_DIR/.env"
MODELS=("gemini" "openai")

# Ask user to select AI model
echo "Select the AI model you want to use:"
select model in "${MODELS[@]}"; do
    if [[ -n "$model" ]]; then
        echo "You selected: $model"
        break
    else
        echo "Invalid selection. Try again."
    fi
done

# Prompt for API key
read -p "Enter your API key for $model: " api_key

# Create config directory if it doesn't exist
mkdir -p "$CONFIG_DIR"

# Write to .env file based on selected model
if [[ "$model" == "gemini" ]]; then
    cat > "$ENV_FILE" <<EOF
GEMINI_API_KEY=$api_key
EOF
elif [[ "$model" == "openai" ]]; then
    cat > "$ENV_FILE" <<EOF
OPENAI_API_KEY=$api_key
EOF
fi

echo "✅ Created .env file at $ENV_FILE"

# Install uv (if not already installed)
if ! command -v uv &> /dev/null; then
    echo "🔧 Downloading uv for Linux users (skip if you have it)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
else
    echo "✅ uv is already installed."
fi

# Create virtual environment
echo "🐍 Creating virtual environment with uv..."
uv venv .venv
source .venv/bin/activate

# Install project dependencies
echo "📦 Installing dependencies from pyproject.toml..."
uv sync

# Run FastAPI server in background
echo "🚀 Starting FastAPI server (main.py)..."
mkdir -p logs
nohup python3 main.py > logs/fastapi.log 2>&1 &

# Run Gradio UI
echo "🎨 Starting Gradio UI (gradio_ui.py)..."
python3 gradio_ui.py &

sleep 3

# Final message
echo ""
echo "✅ Application is running!"
echo "🔗 Visit the Gradio UI at: http://127.0.0.1:7861"
