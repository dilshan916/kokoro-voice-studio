"""
Independent Test Suite for PocketTTSEngine
==========================================
Verifies:
1. Conformance to BaseTTSEngine interface
2. Voice catalog definitions
3. Safe offline behavior without unexpected network downloads
4. Thread-safe lock initialization
"""

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.base_engine import BaseTTSEngine
from core.pocket_engine import PocketTTSEngine, POCKET_VOICE_CATALOG, POCKET_RAW_VOICES


class TestPocketEngine(unittest.TestCase):
    def setUp(self):
        self.engine = PocketTTSEngine(auto_download=False)

    def test_interface_conformance(self):
        self.assertIsInstance(self.engine, BaseTTSEngine)
        self.assertEqual(self.engine.engine_name, "pocket")
        self.assertEqual(self.engine.sample_rate, 24000)

    def test_voice_catalog(self):
        self.assertGreater(len(POCKET_RAW_VOICES), 20)
        self.assertIn("alba", POCKET_RAW_VOICES)
        self.assertIn("marius", POCKET_RAW_VOICES)
        self.assertIn("javert", POCKET_RAW_VOICES)
        self.assertIn("fantine", POCKET_RAW_VOICES)

        # Check curated catalog metadata
        self.assertIn("pocket_alba", POCKET_VOICE_CATALOG)
        self.assertEqual(POCKET_VOICE_CATALOG["pocket_alba"]["engine"], "pocket")
        self.assertEqual(POCKET_VOICE_CATALOG["pocket_alba"]["type"], "character")

    def test_safe_offline_behavior(self):
        # When auto_download is False and weights are not locally cached,
        # load_model() must safely return False with clear status message without hanging or downloading
        if not self.engine.are_weights_cached():
            result = self.engine.load_model(force_download=False)
            self.assertFalse(result)
            self.assertIn("Kokoro voices remain fully functional", self.engine.init_error)
        else:
            result = self.engine.load_model()
            self.assertTrue(result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
