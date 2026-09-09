import sqlite3
import datetime
import secrets
from pathlib import Path

# Connect to SQLite DB
db_path = Path("/home/ubuntu/kokoro-server/data/billing.db")
conn = sqlite3.connect(str(db_path))
cur = conn.cursor()

now = datetime.datetime.now(datetime.timezone.utc).isoformat()
count = 30
prefix = "KOKORO-PRO"
note = "Single-Use 1-Time VIP License Key"

generated_codes = []
for _ in range(count):
    part1 = secrets.token_hex(2).upper()
    part2 = secrets.token_hex(2).upper()
    code = f"{prefix}-{part1}-{part2}"
    cur.execute(
        "INSERT INTO license_keys (code, tier, max_uses, used_count, note, created_at) VALUES (?, 'pro', 1, 0, ?, ?)",
        (code, note, now),
    )
    generated_codes.append(code)

conn.commit()

# Save text file on server
with open("/home/ubuntu/kokoro-server/SINGLE_USE_PROMO_CODES.txt", "w") as f:
    f.write("=" * 60 + "\n")
    f.write("      KOKORO VOICE STUDIO PRO — SINGLE-USE LICENSE CODES\n")
    f.write("=" * 60 + "\n")
    f.write(f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"Total Codes: {len(generated_codes)}\n")
    f.write("Each code below can be redeemed ONCE by 1 user/device.\n")
    f.write("-" * 60 + "\n\n")
    for i, c in enumerate(generated_codes, 1):
        f.write(f"{i:02d}. {c}\n")
    f.write("\n" + "=" * 60 + "\n")

print(f"Generated {count} single-use codes!")
