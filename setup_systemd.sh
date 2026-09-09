#!/bin/bash
set -e

sudo tee /etc/systemd/system/kokoro.service > /dev/null <<EOF
[Unit]
Description=Kokoro Voice Studio Pro FastAPI Backend
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/kokoro-server
ExecStart=/home/ubuntu/kokoro-server/venv/bin/python server.py
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1
Environment=PORT=8000
Environment=HOST=0.0.0.0

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable kokoro
sudo systemctl restart kokoro
sleep 3
sudo systemctl status kokoro --no-pager
