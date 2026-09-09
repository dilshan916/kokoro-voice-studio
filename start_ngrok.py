import sys
import time
import os
import subprocess
import socket
from pyngrok import ngrok, conf

AUTHTOKEN = "3Cxa4FtuSzZjOdCZaIfAnuZ8dyz_4r9uV9RhHkchJyY1abHbK"
DOMAIN = "dry-eldercare-bok.ngrok-free.dev"
PORT = 8000

print("\n" + "=" * 60)
print("  Kokoro Voice Studio Pro - Permanent Ngrok Cloud Server")
print(f"  Fixed Domain: https://{DOMAIN}")
print("=" * 60 + "\n")

# Set authtoken in configuration
conf.get_default().auth_token = AUTHTOKEN

# Function to check if port 8000 is already active
def is_port_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

server_process = None
if not is_port_open(PORT):
    print("[*] Starting Kokoro FastAPI Backend on port 8000...")
    server_process = subprocess.Popen([sys.executable, "server.py"], cwd=os.path.dirname(os.path.abspath(__file__)))
    time.sleep(3)
else:
    print("[*] Kokoro FastAPI Backend is already running on port 8000.")

# Connect Ngrok tunnel with your permanent static domain
print(f"[*] Binding public domain https://{DOMAIN} to port {PORT}...")
try:
    tunnel = ngrok.connect(PORT, domain=DOMAIN)
    print("\n" + "=" * 60)
    print("  🟢 PERMANENT SERVER URL IS LIVE (SSL SECURED):")
    print(f"  --> {tunnel.public_url}")
    print("=" * 60 + "\n")
    print("1. In Kokoro Mobile App -> Settings -> Select 'LAN Studio Sync'")
    print(f"2. Enter URL: {tunnel.public_url}")
    print("3. Tap Save -> Enjoy permanent instant cloud TTS from anywhere!\n")
    print("Press Ctrl+C to stop the server.\n")

    ngrok_process = ngrok.get_ngrok_process()
    ngrok_process.proc.wait()
except KeyboardInterrupt:
    print("\n[*] Shutting down Kokoro server & tunnel...")
    if server_process:
        server_process.terminate()
    ngrok.kill()
except Exception as e:
    print(f"[!] Ngrok connection error: {e}")
    if server_process:
        server_process.terminate()
