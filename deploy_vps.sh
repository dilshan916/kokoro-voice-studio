#!/usr/bin/env bash
# ==============================================================================
# SayTTS (Kokoro Voice Studio Pro) — Production VPS Deployment Script
# ==============================================================================
# Target Host: Ubuntu VPS (/home/ubuntu/kokoro-server)
# Service: systemd kokoro.service (Port 8000 -> https://saytts.site)
# ==============================================================================

set -e

echo ""
echo "=========================================================="
echo "  [*] SayTTS Dual-Engine Production Deployment"
echo "=========================================================="
echo ""

APP_DIR="/home/ubuntu/kokoro-server"
cd "$APP_DIR"

# 1. Pull latest repository changes
echo "[1/6] Pulling latest updates from Git..."
git pull origin main

# 2. Activate Python virtual environment and install dependencies
echo "[2/6] Updating Python virtual environment dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 3. Ensure required directories exist with write permissions
echo "[3/6] Setting up persistent storage directories..."
mkdir -p data/custom_voices data/temp_audio output assets/kokoro

# 4. Compile React 19 production frontend bundle
echo "[4/6] Building production frontend assets..."
cd frontend
npm install
npm run build
cd ..

# 5. Pre-warm / Cache Pocket TTS model weights on fast VPS connection (optional/graceful)
echo "[5/6] Checking Pocket TTS weights..."
python -c "
try:
    from pocket_tts import TTSModel
    print('Checking / downloading Pocket TTS weights on VPS network...')
    TTSModel.load_model()
    print('Pocket TTS model weights are cached and ready!')
except Exception as e:
    print('Note: Pocket TTS download deferred:', e)
" || true

# 6. Restart systemd service and check health
echo "[6/6] Restarting kokoro.service daemon..."
sudo systemctl daemon-reload
sudo systemctl restart kokoro
sleep 3

echo ""
echo "=== Service Status ==="
sudo systemctl status kokoro --no-pager --lines=10

echo ""
echo "=== Health Check ==="
curl -s http://127.0.0.1:8000/health | python -m json.tool | head -n 15 || echo "Server starting up..."

echo ""
echo "=========================================================="
echo "  [✓] Deployment complete! Live at https://saytts.site"
echo "=========================================================="
echo ""
