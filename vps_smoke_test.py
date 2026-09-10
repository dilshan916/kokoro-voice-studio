import urllib.request
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_vps():
    print("\n" + "=" * 55)
    print("  SayTTS Live VPS Production Smoke Test")
    print("=" * 55)

    # 1. Health Check & Kokoro Catalog
    print("\n[1/3] Testing GET /health...")
    req = urllib.request.Request(f"{BASE_URL}/health")
    with urllib.request.urlopen(req, timeout=10) as resp:
        assert resp.status == 200, f"Expected 200, got {resp.status}"
        data = json.loads(resp.read().decode("utf-8"))
        status = data.get("status")
        voices = data.get("voices", [])
        print(f"  -> Engine Status: {status}")
        print(f"  -> Total Catalog Voices: {len(voices)}")
        assert len(voices) == 60, f"Expected exactly 60 Kokoro voices, got {len(voices)}"

        pocket_voices = [v for v in voices if "pocket" in v.get("id", "").lower()]
        assert len(pocket_voices) == 0, f"Expected 0 pocket voices, found {len(pocket_voices)}"
        print("  -> Pocket Voices Count: 0 (Cleanly Removed)")

    # 2. Synthesis via POST /render (Kokoro af_bella)
    print("\n[2/3] Testing POST /render with Kokoro af_bella...")
    payload = json.dumps({
        "text": "SayTTS studio narration platform running purely on Kokoro-82M.",
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
            print(f"  -> Voice: {res_data.get('voice_name')}")
            print(f"  -> Audio Filename: {res_data.get('filename')}")
            print(f"  -> Audio Duration: {res_data.get('duration')}s")
            print(f"  -> Sample Rate: {res_data.get('sample_rate')} Hz")
            print(f"  -> Server Render Latency: {elapsed:.2f}s")
            assert res_data.get("sample_rate") == 24000
            assert res_data.get("duration") > 0
    except urllib.error.HTTPError as http_err:
        print("HTTP Error response body:", http_err.read().decode("utf-8"))
        raise http_err

    # 3. Confirm Pocket/Custom Endpoints are Removed
    print("\n[3/3] Testing removed endpoints (GET /api/voices/custom)...")
    req = urllib.request.Request(f"{BASE_URL}/api/voices/custom")
    try:
        urllib.request.urlopen(req, timeout=10)
        raise AssertionError("Expected 404 for removed /api/voices/custom endpoint!")
    except urllib.error.HTTPError as e:
        print(f"  -> /api/voices/custom response: {e.code} (Correctly 404 Not Found)")
        assert e.code == 404

    print("\n" + "=" * 55)
    print("  [PASS] ALL CLEAN KOKORO PRODUCTION CHECKS PASSED!")
    print("=" * 55 + "\n")

if __name__ == "__main__":
    test_vps()
