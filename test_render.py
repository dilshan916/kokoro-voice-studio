import sys
import os
import traceback

sys.path.insert(0, '/home/ubuntu/kokoro-server')
os.chdir('/home/ubuntu/kokoro-server')

try:
    from core.kokoro_engine import KokoroStudioEngine
    engine = KokoroStudioEngine()
    print("Loading model...")
    engine.load_model()
    print("Synthesizing speech via synthesize_text...")
    samples, sr = engine.synthesize_text('Hello from Oracle Cloud! Your dedicated TTS server is live 24/7.', voice='af_heart')
    print(f"✅ Success! Samples: {len(samples)}, SR: {sr}, Duration: {len(samples)/sr:.2f}s")
except Exception as e:
    traceback.print_exc()
