import sqlite3
import datetime
from pathlib import Path

db_path = Path("/home/ubuntu/kokoro-server/data/billing.db")
conn = sqlite3.connect(str(db_path))
cur = conn.cursor()

now = datetime.datetime.now(datetime.timezone.utc).isoformat()
codes = [
    ('KOKORO-UNLIMITED', 'pro', -1, 0, 'Lifetime VIP Unlimited (All Features)', now),
    ('VIP-CREATOR-2026', 'pro', -1, 0, 'Lifetime Creator Pass (Unlimited)', now),
    ('KOKORO-PRO-LIFETIME', 'pro', -1, 0, 'Lifetime Pro Access', now),
]

cur.executemany(
    "INSERT OR REPLACE INTO license_keys (code, tier, max_uses, used_count, note, created_at) VALUES (?, ?, ?, ?, ?, ?)",
    codes
)
conn.commit()

# Also make all existing registered devices Pro tier immediately
cur.execute("UPDATE devices SET tier = 'pro', note = 'Lifetime VIP Auto-Grant', updated_at = ?", (now,))
conn.commit()

print("🎉 Successfully activated unlimited VIP license keys & upgraded devices to PRO!")
