#!/bin/bash
set -e

# --- 1. Check and install uv if needed ---
OS_TYPE=$(uname -s)

if command -v uv &> /dev/null; then
    echo "uv is already installed."
else
    if [[ "$OS_TYPE" == "Linux" || "$OS_TYPE" == "Darwin" ]]; then
        echo "uv not found. Installing for $OS_TYPE..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        echo "uv installed successfully."
    else
        echo "'uv' is not installed and automatic installation is only supported on Linux and macOS."
        echo "Please install it manually from: https://docs.astral.sh/uv/"
        exit 1
    fi
fi


# --- 2. Dependency Setup ---
spinner() {
    local pid=$1
    local delay=0.1
    local spinstr='|/-\'
    echo -n "Installing dependencies from pyproject.toml... "
    while kill -0 "$pid" 2>/dev/null; do
        for (( i=0; i<${#spinstr}; i++ )); do
            echo -ne "\rInstalling dependencies from pyproject.toml... ${spinstr:$i:1}"
            sleep $delay
        done
    done
    echo -ne "\rDependencies installed!           \n"
}

echo "Creating virtual environment with uv..."
uv venv .venv

# Activate virtual environment
source .venv/bin/activate

# Ensure logs folder exists
mkdir -p logs

# Install dependencies with spinner
uv sync > logs/install.log 2>&1 &
pid=$!
spinner $pid
wait $pid

echo "Setup complete."

# --- 3. Launch FastAPI server ---
echo "Starting FastAPI server (fastapi_app.py)..."
nohup python3 fastapi_app.py > logs/fastapi.log 2>&1 &
fastapi_pid=$!

# Wait for FastAPI to start
sleep 3

# --- 4. Launch Gradio UI ---
echo "Starting Gradio UI (gradio_ui.py)..."
python3 gradio_ui.py &
gradio_pid=$!

sleep 3

# --- 5. Gradio Port Detection ---
GRADIO_PORT=""
GRADIO_URL=$(ps aux | grep "[g]radio_ui.py" | grep -o "http://127.0.0.1:[0-9]\+" || true)

if [[ -n "$GRADIO_URL" ]]; then
    GRADIO_PORT="${GRADIO_URL##*:}"  # Extract port after last colon
else
    for port in {7860..7870}; do
        if nc -z 127.0.0.1 "$port" 2>/dev/null; then
            GRADIO_PORT=$port
            break
        fi
    done
fi

if [[ -z "$GRADIO_PORT" ]]; then
    GRADIO_PORT=7860
fi

# --- 6. Save PIDs for cleanup ---
CONFIG_DIR="config"
mkdir -p "$CONFIG_DIR"
PID_FILE="$CONFIG_DIR/pids.txt"

cat > "$PID_FILE" <<EOF
FASTAPI_PID=$fastapi_pid
GRADIO_PID=$gradio_pid
EOF

# --- 7. Output Info ---
echo ""
echo "Application is running!"
echo "FastAPI Server: http://127.0.0.1:8000"
echo ">>>> GO TO, Gradio UI:      http://127.0.0.1:$GRADIO_PORT"
echo ""
echo "PIDs saved to $PID_FILE for cleanup:"
echo "FastAPI PID: $fastapi_pid"
echo "Gradio PID:  $gradio_pid"

# --- 8. Create cleanup script ---
cat > cleanup.sh <<'EOF'
#!/bin/bash
CONFIG_DIR="config"
PID_FILE="$CONFIG_DIR/pids.txt"

if [[ -f "$PID_FILE" ]]; then
    source "$PID_FILE"

    echo "Stopping FastAPI server (PID: $FASTAPI_PID)..."
    kill "$FASTAPI_PID" 2>/dev/null || echo "FastAPI process not found or already stopped."

    echo "Stopping Gradio UI (PID: $GRADIO_PID)..."
    kill "$GRADIO_PID" 2>/dev/null || echo "Gradio process not found or already stopped."

    rm "$PID_FILE"
    echo "Cleanup complete!"
else
    echo "No PID file found. Trying to kill processes by name..."
    pkill -f "fastapi_app.py" 2>/dev/null || echo "No fastapi_app.py processes found"
    pkill -f "gradio_ui.py" 2>/dev/null || echo "No gradio_ui.py processes found"
fi
EOF

chmod +x cleanup.sh
echo "Run './cleanup.sh' to stop all services."
