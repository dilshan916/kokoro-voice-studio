import urllib.request
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_vps():
    print("\n" + "=" * 55)
    print("  SayTTS Live VPS Production Smoke Test")
    print("=" * 55)

    # 1. Health Check & Unified Catalog
    print("\n[1/3] Testing GET /health...")
    req = urllib.request.Request(f"{BASE_URL}/health")
    with urllib.request.urlopen(req, timeout=10) as resp:
        assert resp.status == 200, f"Expected 200, got {resp.status}"
        data = json.loads(resp.read().decode("utf-8"))
        status = data.get("status")
        voices = data.get("voices", [])
        print(f"  -> Engine Status: {status}")
        print(f"  -> Total Catalog Voices: {len(voices)}")
        assert len(voices) >= 86, f"Expected at least 86 voices, got {len(voices)}"

        kokoro_count = sum(1 for v in voices if v.get("engine") == "kokoro")
        pocket_count = sum(1 for v in voices if v.get("engine") == "pocket")
        print(f"  -> Kokoro Standard Voices: {kokoro_count}")
        print(f"  -> Pocket Character Voices: {pocket_count}")
        assert kokoro_count == 60, f"Expected 60 Kokoro voices, got {kokoro_count}"
        assert pocket_count == 26, f"Expected 26 Pocket voices, got {pocket_count}"

    # 2. Synthesis via POST /render (Kokoro af_bella)
    print("\n[2/3] Testing POST /render with Kokoro af_bella...")
    payload = json.dumps({
        "text": "SayTTS dual engine platform is running live in production.",
        "voice_id": "af_bella",
        "speed": 1.0,
        "eq_preset": "Clean Studio (Default)",
    }).encode("utf-8")

    t0 = time.perf_counter()
    req = urllib.request.Request(
        f"{BASE_URL}/render",
        data=payload,
        headers={"Content-Type": "application/json", "X-Device-Id": "vps_smoke_tester"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            elapsed = time.perf_counter() - t0
            assert resp.status == 200, f"Expected 200, got {resp.status}"
            res_data = json.loads(resp.read().decode("utf-8"))
            print(f"  -> Success: {res_data.get('success')}")
            print(f"  -> Audio Filename: {res_data.get('filename')}")
            print(f"  -> Audio Duration: {res_data.get('duration')}s")
            print(f"  -> Sample Rate: {res_data.get('sample_rate')} Hz")
            print(f"  -> Has Base64 Stream: {bool(res_data.get('audio_base64'))}")
            print(f"  -> Has Subtitles (.srt): {bool(res_data.get('srt_content'))}")
            print(f"  -> Server Render Latency: {elapsed:.2f}s")
            assert res_data.get("sample_rate") == 24000
            assert res_data.get("duration") > 0
    except urllib.error.HTTPError as http_err:
        print("HTTP Error response body:", http_err.read().decode("utf-8"))
        raise http_err

    # 3. Custom Voice Endpoints Check
    print("\n[3/3] Testing GET /api/voices/custom...")
    req = urllib.request.Request(
        f"{BASE_URL}/api/voices/custom",
        headers={"X-Device-Id": "vps_smoke_tester"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        assert resp.status == 200
        c_data = json.loads(resp.read().decode("utf-8"))
        print(f"  -> Custom Voices Count: {len(c_data.get('voices', []))}")
        print("  -> Device-isolated custom voices endpoint: OK")

    print("\n" + "=" * 55)
    print("  [PASS] ALL LIVE VPS CHECKS PASSED SUCCESSFULLY!")
    print("=" * 55 + "\n")

if __name__ == "__main__":
    test_vps()
