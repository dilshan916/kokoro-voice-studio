"""
Kokoro Voice Studio Pro — Native Windows Desktop Launcher
=========================================================
Lead Developer: Dilshan Chandrarathne
Starts the unified FastAPI + React 19 local web app and launches
a frameless native Windows desktop window using Microsoft Edge App Mode.
"""

from __future__ import annotations

import os
import sys
import time
import socket
import subprocess
import threading
import webbrowser
import multiprocessing as mp
from pathlib import Path

# Guard against None stdout/stderr in windowless PyInstaller builds
if sys.stdout is None:
    try:
        sys.stdout = open(os.devnull, "w", encoding="utf-8", errors="ignore")
    except Exception:
        pass

if sys.stderr is None:
    try:
        sys.stderr = open(os.devnull, "w", encoding="utf-8", errors="ignore")
    except Exception:
        pass

# Configure Windows UTF-8 encoding
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def find_free_port(starting_port: int = 8000) -> int:
    """Find an available TCP port starting from starting_port."""
    for port in range(starting_port, starting_port + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    return starting_port


def wait_for_server(url: str, timeout: float = 60.0) -> bool:
    """Wait until the FastAPI health endpoint responds successfully."""
    import urllib.request
    import urllib.error

    start = time.time()
    health_url = f"{url.rstrip('/')}/health"
    last_reported = 0
    while time.time() - start < timeout:
        elapsed = int(time.time() - start)
        if elapsed > 0 and elapsed != last_reported and elapsed % 3 == 0:
            print(f"[*] Starting local neural server... ({elapsed}s elapsed)")
            last_reported = elapsed
        try:
            with urllib.request.urlopen(health_url, timeout=2.0) as resp:
                if resp.status == 200:
                    time.sleep(0.4)  # Ensure port & routes are fully established
                    return True
        except Exception:
            time.sleep(0.25)
    return False


def get_edge_path() -> str | None:
    """Locate Microsoft Edge executable on Windows."""
    candidates = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None


def get_chrome_path() -> str | None:
    """Locate Google Chrome executable on Windows."""
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None


def launch_native_window(app_url: str) -> None:
    """
    Launch native Windows App Mode window without browser address bars,
    giving a 100% native desktop application look & feel.
    """
    edge_bin = get_edge_path()
    chrome_bin = get_chrome_path()

    # Create a lightweight isolated profile directory for the desktop window session
    user_data_dir = os.path.join(os.environ.get("TEMP", os.getcwd()), "KokoroStudio_DesktopProfile")
    os.makedirs(user_data_dir, exist_ok=True)

    if edge_bin:
        cmd = [
            edge_bin,
            f"--app={app_url}",
            "--window-size=1380,880",
            f"--user-data-dir={user_data_dir}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-features=Translate",
            "--app-id=kokorovoicestudio",
        ]
        try:
            proc = subprocess.Popen(cmd)
            proc.wait()
            return
        except Exception as e:
            print(f"[WARN] Edge App Mode launch failed: {e}")

    if chrome_bin:
        cmd = [
            chrome_bin,
            f"--app={app_url}",
            "--window-size=1380,880",
            f"--user-data-dir={user_data_dir}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-features=Translate",
        ]
        try:
            proc = subprocess.Popen(cmd)
            proc.wait()
            return
        except Exception as e:
            print(f"[WARN] Chrome App Mode launch failed: {e}")

    # Fallback to system default browser
    webbrowser.open(app_url)


def run_server(host: str, port: int, server_holder: list) -> None:
    """Start Uvicorn server in background thread with dedicated asyncio event loop."""
    import asyncio
    import uvicorn
    from server import app

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    config = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level="warning",
        loop="asyncio",
    )
    server = uvicorn.Server(config)
    server.install_signal_handlers = lambda: None
    server_holder.append((server, loop))

    try:
        loop.run_until_complete(server.serve())
    except Exception as e:
        print(f"[ERROR] Server error: {e}")


def main() -> None:
    # Essential for Windows PyInstaller multiprocessing
    mp.freeze_support()

    host = "0.0.0.0"
    port = find_free_port(8000)
    app_url = f"http://127.0.0.1:{port}"

    print("=" * 60)
    print("  Kokoro Voice Studio Pro (Desktop & Mobile Sync Edition)")
    print("  Lead Developer: Dilshan Chandrarathne")
    print(f"  Local Studio URL: {app_url}")
    print(f"  Mobile LAN Access: http://<your-pc-ip>:{port}")
    print("=" * 60)

    server_holder: list = []

    # Start FastAPI server in background thread
    server_thread = threading.Thread(
        target=run_server,
        args=(host, port, server_holder),
        daemon=True,
    )
    server_thread.start()

    # Wait for server readiness
    print("[*] Initializing neural speech engine & studio interface...")
    ready = wait_for_server(app_url, timeout=60.0)
    if not ready:
        print("[ERROR] Kokoro studio backend did not respond within 60 seconds.")
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(
                0,
                "Kokoro Voice Studio local backend server failed to initialize. Please check if another app is blocking port connections.",
                "Kokoro Voice Studio — Startup Error",
                0x10,
            )
        except Exception:
            pass
        sys.exit(1)

    # Launch desktop application window only after server is 100% verified live
    print("[*] Studio backend ready! Launching Kokoro Voice Studio Pro Window...")
    launch_native_window(app_url)

    print("[*] Application window closed. Shutting down studio...")
    if server_holder:
        srv, _ = server_holder[0]
        srv.should_exit = True
    sys.exit(0)


if __name__ == "__main__":
    main()
