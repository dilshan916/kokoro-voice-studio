"""
Test Suite for TTSRouter
========================
Verifies:
1. Engine resolution for Kokoro voices ('af_bella', 'am_adam') -> 'kokoro'
2. Engine resolution for Pocket voices ('pocket_alba', 'pocket_marius') -> 'pocket'
3. Engine resolution for custom voices ('custom_12345') -> 'pocket'
4. Full Kokoro synthesis execution via router
5. Unified voice catalog generation with engine/type tags
"""

import sys
import unittest
from pathlib import Path
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.tts_router import TTSRouter


class TestTTSRouter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.router = TTSRouter()
        cls.router.kokoro.load_model()

    def test_engine_resolution(self):
        # Standard Kokoro voices
        self.assertEqual(self.router.resolve_engine_for_voice("af_bella"), "kokoro")
        self.assertEqual(self.router.resolve_engine_for_voice("am_adam"), "kokoro")
        self.assertEqual(self.router.resolve_engine_for_voice("jf_alpha"), "kokoro")
        self.assertEqual(self.router.resolve_engine_for_voice(""), "kokoro")
        self.assertEqual(self.router.resolve_engine_for_voice(None), "kokoro")

        # Pocket character voices
        self.assertEqual(self.router.resolve_engine_for_voice("pocket_alba"), "pocket")
        self.assertEqual(self.router.resolve_engine_for_voice("pocket_marius"), "pocket")
        self.assertEqual(self.router.resolve_engine_for_voice("alba"), "pocket")

        # Custom voices
        self.assertEqual(self.router.resolve_engine_for_voice("custom_abc123"), "pocket")
        self.assertEqual(self.router.resolve_engine_for_voice("path/to/voice.safetensors"), "pocket")

    def test_router_synthesis_kokoro(self):
        samples, sr, engine_used = self.router.synthesize(
            text="Router Kokoro verification.",
            voice="af_bella",
        )
        self.assertEqual(engine_used, "kokoro")
        self.assertEqual(sr, 24000)
        self.assertIsInstance(samples, np.ndarray)
        self.assertGreater(len(samples), 1000)

    def test_unified_catalog(self):
        custom_mock = [{
            "id": "custom_test_1",
            "name": "My Cloned Voice",
            "lang": "en-us",
            "gender": "Male",
        }]
        catalog = self.router.get_unified_catalog(custom_voices=custom_mock)
        self.assertGreater(len(catalog), 60)

        # Verify engine tags exist on all items
        for item in catalog:
            self.assertIn("engine", item)
            self.assertIn(item["engine"], ["kokoro", "pocket"])
            self.assertIn("type", item)
            self.assertIn(item["type"], ["standard", "custom", "character"])

        # Find custom item
        custom_item = next(i for i in catalog if i["id"] == "custom_test_1")
        self.assertEqual(custom_item["engine"], "pocket")
        self.assertEqual(custom_item["type"], "custom")


if __name__ == "__main__":
    unittest.main(verbosity=2)
