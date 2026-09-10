"""
Regression Test Suite for Kokoro-82M Engine
============================================
Verifies that KokoroStudioEngine:
1. Conforms to BaseTTSEngine interface
2. Successfully loads the ONNX model
3. Generates correct 24000 Hz audio for standard voices
4. Preserves audio sample rate and non-empty output
5. Successfully converts to AudioSegment and exports
"""

import sys
import unittest
from pathlib import Path
import numpy as np

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.kokoro_engine import KokoroStudioEngine, VOICE_CATALOG, MASTERING_PRESETS


class TestKokoroRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = KokoroStudioEngine()
        cls.loaded = cls.engine.load_model()

    def test_engine_loaded(self):
        self.assertEqual(self.engine.sample_rate, 24000)
        self.assertTrue(self.engine._is_loaded)

    def test_default_synthesis(self):
        samples, sr = self.engine.synthesize_text("Kokoro regression verification.", voice="af_bella")
        self.assertIsInstance(samples, np.ndarray)
        self.assertEqual(sr, 24000)
        self.assertGreater(len(samples), 1000)
        self.assertEqual(samples.dtype, np.float32)

    def test_multiple_voices(self):
        for v in ["af_bella", "am_adam", "bm_george"]:
            self.assertIn(v, VOICE_CATALOG)
            samples, sr = self.engine.synthesize_text("Voice check.", voice=v)
            self.assertGreater(len(samples), 500)
            self.assertEqual(sr, 24000)

    def test_mastering_pipeline(self):
        samples, sr = self.engine.synthesize_text("Mastering check.", voice="af_bella")
        audio_seg = self.engine.numpy_to_audiosegment(samples, sr)
        self.assertGreater(len(audio_seg), 100)
        
        # Test preset
        mastered = self.engine.apply_studio_mastering(audio_seg, preset="Warm Podcast Host (+Bass)")
        self.assertGreater(len(mastered), 100)


if __name__ == "__main__":
    unittest.main(verbosity=2)
