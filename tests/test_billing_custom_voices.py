import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.billing_db import BillingDB


class TestBillingCustomVoices(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.db_path = os.path.join(self.temp_dir.name, "test_billing.db")
        self.db = BillingDB(self.db_path)

    def tearDown(self):
        import gc
        gc.collect()
        self.temp_dir.cleanup()

    def test_custom_voice_crud_and_isolation(self):
        # Create dummy state and audio files
        state_file = os.path.join(self.temp_dir.name, "custom_v1.safetensors")
        with open(state_file, "wb") as f:
            f.write(b"dummy_weights")

        audio_file = os.path.join(self.temp_dir.name, "ref.wav")
        with open(audio_file, "wb") as f:
            f.write(b"dummy_audio")

        # 1. Create voice for device A
        created = self.db.create_custom_voice(
            device_id="dev_A",
            voice_id="custom_v1",
            name="Alice Custom",
            state_file_path=state_file,
            reference_audio_path=audio_file,
            duration_sec=5.2,
            engine="pocket"
        )
        self.assertEqual(created["id"], "custom_v1")
        self.assertEqual(created["name"], "Alice Custom")
        self.assertEqual(created["engine"], "pocket")
        self.assertEqual(created["type"], "custom")
        self.assertNotIn("state_file_path", created)
        self.assertNotIn("reference_audio_path", created)

        # 2. List voices for device A
        voices_a = self.db.get_custom_voices("dev_A")
        self.assertEqual(len(voices_a), 1)
        self.assertEqual(voices_a[0]["id"], "custom_v1")
        self.assertNotIn("state_file_path", voices_a[0])
        self.assertNotIn("reference_audio_path", voices_a[0])

        # 3. Isolation: Device B should see 0 voices
        voices_b = self.db.get_custom_voices("dev_B")
        self.assertEqual(len(voices_b), 0)

        # 4. Internal lookup by id includes state path for backend synthesis
        internal = self.db.get_custom_voice_by_id("custom_v1")
        self.assertIsNotNone(internal)
        self.assertEqual(internal["state_file_path"], state_file)

        # 5. Device B cannot delete Device A's voice
        del_b = self.db.delete_custom_voice("dev_B", "custom_v1")
        self.assertIsNone(del_b)
        self.assertTrue(os.path.exists(state_file))

        # 6. Device A can delete own voice
        del_a = self.db.delete_custom_voice("dev_A", "custom_v1")
        self.assertEqual(del_a, state_file)
        self.assertFalse(os.path.exists(state_file))
        self.assertFalse(os.path.exists(audio_file))

        # 7. List for A is now empty
        self.assertEqual(len(self.db.get_custom_voices("dev_A")), 0)


if __name__ == "__main__":
    unittest.main()
