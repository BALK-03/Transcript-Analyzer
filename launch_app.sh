#!/bin/bash

set -e

CONFIG_DIR="config"
ENV_FILE="$CONFIG_DIR/.env"
SERVER_CONFIG="$CONFIG_DIR/server_config.json"

echo "The select AI model Gemini:"

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

echo -e "\rDependencies installed!"

echo "Starting FastAPI server (main.py)..."
mkdir -p logs
nohup python3 main.py > logs/fastapi.log 2>&1 &
fastapi_pid=$!

# Wait a moment for FastAPI to start and detect its port
sleep 3

# Method 1: Try to detect FastAPI port from log file
FASTAPI_PORT=$(grep -o "http://127.0.0.1:[0-9]*" logs/fastapi.log 2>/dev/null | head -1 | grep -o "[0-9]*$" || echo "8000")

# Method 2: Alternative - scan for open ports (if log method fails)
if [[ "$FASTAPI_PORT" == "8000" ]] && ! nc -z 127.0.0.1 8000 2>/dev/null; then
    echo "Scanning for FastAPI port..."
    for port in {8000..8010}; do
        if nc -z 127.0.0.1 $port 2>/dev/null; then
            FASTAPI_PORT=$port
            break
        fi
    done
fi

API_URL="http://127.0.0.1:${FASTAPI_PORT}/pipeline"

# Save the API URL to config file
cat > "$SERVER_CONFIG" <<EOF
{
    "api_url": "$API_URL",
    "fastapi_port": $FASTAPI_PORT
}
EOF

# Export API_URL as environment variable for Gradio
export API_URL="$API_URL"

echo "FastAPI detected on port: $FASTAPI_PORT"
echo "API URL: $API_URL"

echo "Starting Gradio UI (gradio_ui.py)..."
python3 gradio_ui.py &
gradio_pid=$!

sleep 3

# Try to detect Gradio port
GRADIO_PORT=$(ps aux | grep "gradio_ui.py" | grep -v grep | head -1 | grep -o "http://127.0.0.1:[0-9]*" || echo "7860")
if [[ "$GRADIO_PORT" == "7860" ]]; then
    # Check common Gradio ports
    for port in {7860..7870}; do
        if nc -z 127.0.0.1 $port 2>/dev/null; then
            GRADIO_PORT=$port
            break
        fi
    done
fi

echo ""
echo "Application is running!"
echo "FastAPI Server: http://127.0.0.1:$FASTAPI_PORT"
echo "Gradio UI: http://127.0.0.1:$GRADIO_PORT"
echo ""
echo "PIDs saved for cleanup:"
echo "FastAPI PID: $fastapi_pid"
echo "Gradio PID: $gradio_pid"

# Save PIDs for cleanup script
cat > "$CONFIG_DIR/pids.txt" <<EOF
FASTAPI_PID=$fastapi_pid
GRADIO_PID=$gradio_pid
EOF

# Create cleanup script
cat > "cleanup.sh" <<'EOF'
#!/bin/bash
CONFIG_DIR="config"
PID_FILE="$CONFIG_DIR/pids.txt"

if [[ -f "$PID_FILE" ]]; then
    source "$PID_FILE"
    
    echo "Stopping FastAPI server (PID: $FASTAPI_PID)..."
    kill $FASTAPI_PID 2>/dev/null || echo "FastAPI process not found"
    
    echo "Stopping Gradio UI (PID: $GRADIO_PID)..."
    kill $GRADIO_PID 2>/dev/null || echo "Gradio process not found"
    
    rm "$PID_FILE"
    echo "Cleanup complete!"
else
    echo "No PID file found. Trying to kill processes by name..."
    pkill -f "main.py" 2>/dev/null || echo "No main.py processes found"
    pkill -f "gradio_ui.py" 2>/dev/null || echo "No gradio_ui.py processes found"
fi
EOF

chmod +x cleanup.sh
echo "Run './cleanup.sh' to stop all services."