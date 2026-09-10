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
    print("\n[2/4] Testing POST /render with Kokoro af_bella...")
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
            print(f"  -> Server Render Latency: {elapsed:.2f}s")
            assert res_data.get("sample_rate") == 24000
    except urllib.error.HTTPError as http_err:
        print("HTTP Error response body:", http_err.read().decode("utf-8"))
        raise http_err

    # 2b. Synthesis via POST /render (Pocket TTS pocket_alba)
    print("\n[3/4] Testing POST /render with Pocket TTS pocket_alba...")
    p_payload = json.dumps({
        "text": "Testing pocket character voice in production.",
        "voice_id": "pocket_alba",
        "speed": 1.0,
        "eq_preset": "Clean Studio (Default)",
    }).encode("utf-8")

    t0 = time.perf_counter()
    p_req = urllib.request.Request(
        f"{BASE_URL}/render",
        data=p_payload,
        headers={"Content-Type": "application/json", "X-Device-Id": "vps_smoke_tester"},
    )
    try:
        with urllib.request.urlopen(p_req, timeout=30) as resp:
            elapsed = time.perf_counter() - t0
            print(f"  -> HTTP Status: {resp.status}")
            p_res_data = json.loads(resp.read().decode("utf-8"))
            print(f"  -> Success: {p_res_data.get('success')}")
            print(f"  -> Audio Filename: {p_res_data.get('filename')}")
            print(f"  -> Duration: {p_res_data.get('duration')}s")
            print(f"  -> Sample Rate: {p_res_data.get('sample_rate')} Hz")
            assert resp.status == 200
            assert p_res_data.get("sample_rate") == 24000
    except urllib.error.HTTPError as http_err:
        print("Pocket TTS HTTP Error Code:", http_err.code)
        print("Pocket TTS Error Detail:", http_err.read().decode("utf-8"))
        raise http_err

    # 2c. Synthesis via POST /render (Pocket TTS pocket_marius)
    print("\n[3b/4] Testing POST /render with Pocket TTS pocket_marius...")
    p2_payload = json.dumps({
        "text": "Testing Marius character male voice.",
        "voice_id": "pocket_marius",
        "speed": 1.0,
    }).encode("utf-8")
    p2_req = urllib.request.Request(
        f"{BASE_URL}/render",
        data=p2_payload,
        headers={"Content-Type": "application/json", "X-Device-Id": "vps_smoke_tester"},
    )
    with urllib.request.urlopen(p2_req, timeout=30) as resp:
        assert resp.status == 200
        p2_res = json.loads(resp.read().decode("utf-8"))
        print(f"  -> Success: {p2_res.get('success')}")
        print(f"  -> Audio Filename: {p2_res.get('filename')}")
        print(f"  -> Duration: {p2_res.get('duration')}s")

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
