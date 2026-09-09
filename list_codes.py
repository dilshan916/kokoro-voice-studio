import sqlite3
from pathlib import Path

db_path = Path("/home/ubuntu/kokoro-server/data/billing.db")
conn = sqlite3.connect(str(db_path))
cur = conn.cursor()

cur.execute("SELECT code, tier, max_uses, used_count, note FROM license_keys")
rows = cur.fetchall()

print("\n📋 ACTIVE PROMO & LICENSE CODES IN YOUR DATABASE:\n")
for r in rows:
    code, tier, max_uses, used_count, note = r
    uses_str = "Unlimited (∞)" if max_uses == -1 else f"{used_count}/{max_uses} used"
    print(f"  • Code: {code:<22} | Uses: {uses_str:<16} | Note: {note}")

cur.execute("SELECT count(*) FROM devices WHERE tier = 'pro'")
pro_count = cur.fetchone()[0]
print(f"\n🌟 Total Active PRO Devices: {pro_count}\n")
