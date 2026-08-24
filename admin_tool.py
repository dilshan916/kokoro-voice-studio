"""
Kokoro Voice Studio Pro — Admin Management CLI Tool
===================================================
Usage Examples:
  # Grant permanent PRO to a friend by Device ID:
  python admin_tool.py grant <device_id>

  # Create a custom VIP Promo Code (e.g. for 10 friends):
  python admin_tool.py create-key --code KOKORO-VIP-FRIENDS --uses 10 --note "Special Discord friends"

  # Create an unlimited lifetime promo key:
  python admin_tool.py create-key --code SPECIAL-VIP --uses -1 --note "VIP lifetime"

  # List all registered devices and their monthly usage:
  python admin_tool.py list-devices

  # List all promo and license keys:
  python admin_tool.py list-keys

  # Reset character usage for a device:
  python admin_tool.py reset-usage <device_id>
"""

import argparse
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from core.billing_db import billing_db

def main():
    parser = argparse.ArgumentParser(description="Kokoro Voice Studio Pro — Admin CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 1. Grant Pro
    grant_parser = subparsers.add_parser("grant", help="Grant Pro status directly to a Device ID")
    grant_parser.add_argument("device_id", help="Target Device ID (e.g. dev_9f8a3c...)")
    grant_parser.add_argument("--tier", default="pro", choices=["free", "pro"], help="Target tier")
    grant_parser.add_argument("--note", default="Admin CLI Grant", help="Administrative note")

    # 2. Create Promo Key
    key_parser = subparsers.add_parser("create-key", help="Create a new Promo / VIP License Code")
    key_parser.add_argument("--code", required=True, help="Promo code string (e.g. VIP-GIFT)")
    key_parser.add_argument("--uses", type=int, default=1, help="Max uses (use -1 for unlimited uses)")
    key_parser.add_argument("--note", default="", help="Note / description")

    # 3. List Devices
    list_dev_parser = subparsers.add_parser("list-devices", help="List registered devices and usage")
    list_dev_parser.add_argument("--limit", type=int, default=50, help="Max devices to display")

    # 4. List Keys
    subparsers.add_parser("list-keys", help="List all promo / license codes")

    # 5. Reset Usage
    reset_parser = subparsers.add_parser("reset-usage", help="Reset monthly usage for a Device ID")
    reset_parser.add_argument("device_id", help="Target Device ID")

    # 6. Check Device
    check_parser = subparsers.add_parser("check", help="Check quota status for a Device ID")
    check_parser.add_argument("device_id", help="Target Device ID")

    args = parser.parse_args()

    if args.command == "grant":
        res = billing_db.grant_pro(args.device_id, tier=args.tier, note=args.note)
        print(f"\n[SUCCESS] Device '{args.device_id}' is now {args.tier.upper()}!")
        print(f"Status: {res}\n")

    elif args.command == "create-key":
        res = billing_db.create_license_key(args.code, max_uses=args.uses, note=args.note)
        print(f"\n[SUCCESS] Created Promo Key: {res['code']}")
        print(f"Max Uses: {'Unlimited' if res['max_uses'] == -1 else res['max_uses']}")
        print(f"Note: {res['note']}\n")

    elif args.command == "list-devices":
        devices = billing_db.list_devices(limit=args.limit)
        print(f"\n{'='*75}")
        print(f" {'DEVICE ID':<30} | {'TIER':<6} | {'USAGE (CHARS)':<14} | {'UPDATED'}")
        print(f"{'='*75}")
        for d in devices:
            usage_str = f"{d['monthly_usage']:,} / {d['monthly_limit']:,}" if d['tier'] == 'free' else f"{d['monthly_usage']:,} (Unlimited)"
            print(f" {d['device_id']:<30} | {d['tier'].upper():<6} | {usage_str:<14} | {d['updated_at'][:19]}")
        print(f"{'='*75}\nTotal devices: {len(devices)}\n")

    elif args.command == "list-keys":
        keys = billing_db.list_license_keys()
        print(f"\n{'='*75}")
        print(f" {'PROMO CODE':<25} | {'USES':<12} | {'NOTE'}")
        print(f"{'='*75}")
        for k in keys:
            uses_str = f"{k['used_count']} / {'Unlimited' if k['max_uses'] == -1 else k['max_uses']}"
            print(f" {k['code']:<25} | {uses_str:<12} | {k['note'] or ''}")
        print(f"{'='*75}\nTotal keys: {len(keys)}\n")

    elif args.command == "reset-usage":
        res = billing_db.reset_device_usage(args.device_id)
        print(f"\n[SUCCESS] Usage reset for device '{args.device_id}'")
        print(f"Status: {res}\n")

    elif args.command == "check":
        res = billing_db.get_device_quota(args.device_id)
        print(f"\n[DEVICE STATUS] {args.device_id}")
        for k, v in res.items():
            print(f"  - {k}: {v}")
        print()

if __name__ == "__main__":
    main()
