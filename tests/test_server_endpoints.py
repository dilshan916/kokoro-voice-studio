import os
import sys
import unittest
from pathlib import Path
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from server import app
from core.billing_db import billing_db


class TestServerEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app, raise_server_exceptions=False)

    def test_health_endpoint_catalog(self):
        """Test GET /health returns all Kokoro (60) and Pocket (26) voices."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("voices", data)
        self.assertGreaterEqual(len(data["voices"]), 86)

        # Verify Kokoro voices have engine='kokoro' and type='standard'
        kokoro_bella = next((v for v in data["voices"] if v["id"] == "af_bella"), None)
        self.assertIsNotNone(kokoro_bella)
        self.assertEqual(kokoro_bella["engine"], "kokoro")
        self.assertEqual(kokoro_bella["type"], "standard")

        # Verify Pocket voices have engine='pocket' and type='character'
        pocket_alba = next((v for v in data["voices"] if v["id"] == "pocket_alba"), None)
        self.assertIsNotNone(pocket_alba)
        self.assertEqual(pocket_alba["engine"], "pocket")
        self.assertEqual(pocket_alba["type"], "character")

    def test_custom_voices_isolation_api(self):
        """Test GET, POST validation, and DELETE for custom voices."""
        # 1. List with device-A
        res_a = self.client.get("/api/voices/custom", headers={"X-Device-Id": "dev_test_A"})
        self.assertEqual(res_a.status_code, 200)
        self.assertEqual(res_a.json(), {"voices": []})

        # 2. Validation: missing name
        res_err1 = self.client.post(
            "/api/voices/custom",
            headers={"X-Device-Id": "dev_test_A"},
            data={"name": ""},
            files={"file": ("test.wav", b"fake wav", "audio/wav")}
        )
        self.assertEqual(res_err1.status_code, 400)

        # 3. Validation: invalid extension
        res_err2 = self.client.post(
            "/api/voices/custom",
            headers={"X-Device-Id": "dev_test_A"},
            data={"name": "My Voice"},
            files={"file": ("test.txt", b"not audio", "text/plain")}
        )
        self.assertEqual(res_err2.status_code, 400)

        # 4. DELETE non-existent returns 404
        res_del = self.client.delete(
            "/api/voices/custom/custom_nonexistent",
            headers={"X-Device-Id": "dev_test_A"}
        )
        self.assertEqual(res_del.status_code, 404)

    def test_unified_route_alias(self):
        """Confirm /api/tts/generate is wired as an alias to /render."""
        # Check invalid empty text returns 422 Unprocessable Entity (standard FastAPI validation)
        res = self.client.post("/api/tts/generate", json={"text": "", "voice_id": "af_bella"})
        self.assertEqual(res.status_code, 422)


if __name__ == "__main__":
    unittest.main()
