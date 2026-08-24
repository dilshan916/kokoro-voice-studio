"""
Kokoro Voice Studio Pro — Billing, Quota & Anonymous Device Management DB
=========================================================================
Persistent SQLite database handling:
  - Anonymous Device ID registry (zero-login)
  - 20,000 characters/month Free Tier enforcement (resets automatically each month)
  - Pro Plan (Unlimited) tier management
  - Promo / VIP License key generation & instant in-app redemption
  - Stripe Customer & Subscription metadata binding
"""

from __future__ import annotations

import datetime
import logging
import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("kokoro.billing")

DEFAULT_FREE_MONTHLY_LIMIT = 20000


class BillingDB:
    """Manages SQLite storage for anonymous device quotas and license keys."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            base_dir = Path(__file__).resolve().parent.parent
            data_dir = base_dir / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = str(data_dir / "billing.db")
        else:
            self.db_path = db_path

        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _current_cycle_month(self) -> str:
        """Returns current year-month string: 'YYYY-MM' (e.g. '2026-08')"""
        return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m")

    def _init_db(self) -> None:
        """Create tables and indexes if they do not already exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 1. Devices Table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS devices (
                    device_id TEXT PRIMARY KEY,
                    tier TEXT NOT NULL DEFAULT 'free',
                    monthly_usage INTEGER NOT NULL DEFAULT 0,
                    monthly_limit INTEGER NOT NULL DEFAULT 20000,
                    billing_cycle_month TEXT NOT NULL,
                    license_key TEXT,
                    stripe_customer_id TEXT,
                    stripe_subscription_id TEXT,
                    note TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

            # 2. License / Promo Keys Table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS license_keys (
                    code TEXT PRIMARY KEY,
                    tier TEXT NOT NULL DEFAULT 'pro',
                    max_uses INTEGER NOT NULL DEFAULT 1,
                    used_count INTEGER NOT NULL DEFAULT 0,
                    note TEXT,
                    created_at TEXT NOT NULL,
                    expires_at TEXT
                )
                """
            )

            # 3. Usage Log Table (for analytics / auditing)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS usage_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT NOT NULL,
                    char_count INTEGER NOT NULL,
                    voice_id TEXT,
                    timestamp TEXT NOT NULL
                )
                """
            )

            conn.commit()

            # Seed default VIP codes if license_keys table is empty
            cursor.execute("SELECT COUNT(*) FROM license_keys")
            count = cursor.fetchone()[0]
            if count == 0:
                now = datetime.datetime.now(datetime.timezone.utc).isoformat()
                default_keys = [
                    ("KOKORO-VIP-FRIEND", "pro", -1, "Unlimited VIP Master Key", now),
                    ("BETA-PRO-2026", "pro", 100, "Beta Tester Key (100 uses)", now),
                ]
                cursor.executemany(
                    "INSERT INTO license_keys (code, tier, max_uses, note, created_at) VALUES (?, ?, ?, ?, ?)",
                    default_keys,
                )
                conn.commit()
                logger.info("Initialized default VIP promo keys: KOKORO-VIP-FRIEND, BETA-PRO-2026")

    def get_or_create_device(self, device_id: str) -> Dict[str, Any]:
        """Fetch device record or create a fresh free-tier profile."""
        if not device_id or not device_id.strip():
            device_id = "dev_anonymous"

        clean_id = device_id.strip()
        current_cycle = self._current_cycle_month()
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM devices WHERE device_id = ?", (clean_id,))
            row = cursor.fetchone()

            if row is None:
                # Create new device profile
                cursor.execute(
                    """
                    INSERT INTO devices (
                        device_id, tier, monthly_usage, monthly_limit,
                        billing_cycle_month, created_at, updated_at
                    ) VALUES (?, 'free', 0, ?, ?, ?, ?)
                    """,
                    (clean_id, DEFAULT_FREE_MONTHLY_LIMIT, current_cycle, now, now),
                )
                conn.commit()
                cursor.execute("SELECT * FROM devices WHERE device_id = ?", (clean_id,))
                row = cursor.fetchone()
            else:
                # Check for monthly cycle reset
                if row["billing_cycle_month"] != current_cycle:
                    cursor.execute(
                        """
                        UPDATE devices
                        SET monthly_usage = 0,
                            billing_cycle_month = ?,
                            updated_at = ?
                        WHERE device_id = ?
                        """,
                        (current_cycle, now, clean_id),
                    )
                    conn.commit()
                    cursor.execute("SELECT * FROM devices WHERE device_id = ?", (clean_id,))
                    row = cursor.fetchone()

            return dict(row)

    def get_device_quota(self, device_id: str) -> Dict[str, Any]:
        """Returns structured quota information for device."""
        device = self.get_or_create_device(device_id)
        tier = device.get("tier", "free")
        usage = device.get("monthly_usage", 0)
        limit = device.get("monthly_limit", DEFAULT_FREE_MONTHLY_LIMIT)
        is_pro = tier == "pro"

        remaining = max(0, limit - usage) if not is_pro else 999999999

        return {
            "device_id": device["device_id"],
            "tier": tier,
            "is_pro": is_pro,
            "monthly_usage": usage,
            "monthly_limit": limit if not is_pro else None,
            "remaining_chars": remaining if not is_pro else "unlimited",
            "percent_used": min(100.0, round((usage / limit) * 100, 1)) if not is_pro and limit > 0 else 0.0,
            "billing_cycle": device["billing_cycle_month"],
            "license_key": device.get("license_key"),
        }

    def check_and_consume_quota(
        self, device_id: str, char_count: int, voice_id: str = ""
    ) -> Tuple[bool, Dict[str, Any], str]:
        """
        Validates whether device has sufficient quota for character length.
        If allowed, records consumption and returns (True, updated_quota, "ok").
        If quota exceeded on free tier, returns (False, quota_info, "quota_exceeded").
        """
        device = self.get_or_create_device(device_id)
        tier = device.get("tier", "free")
        usage = device.get("monthly_usage", 0)
        limit = device.get("monthly_limit", DEFAULT_FREE_MONTHLY_LIMIT)

        # Pro users have unlimited access
        if tier == "pro":
            with self._get_connection() as conn:
                cursor = conn.cursor()
                now = datetime.datetime.now(datetime.timezone.utc).isoformat()
                cursor.execute(
                    "UPDATE devices SET monthly_usage = monthly_usage + ?, updated_at = ? WHERE device_id = ?",
                    (char_count, now, device["device_id"]),
                )
                cursor.execute(
                    "INSERT INTO usage_logs (device_id, char_count, voice_id, timestamp) VALUES (?, ?, ?, ?)",
                    (device["device_id"], char_count, voice_id, now),
                )
                conn.commit()
            return True, self.get_device_quota(device_id), "ok"

        # Free tier limit check
        if usage + char_count > limit:
            remaining = max(0, limit - usage)
            return (
                False,
                self.get_device_quota(device_id),
                f"Monthly free Cloud GPU quota exceeded ({usage:,} / {limit:,} chars used). Remaining: {remaining:,} chars. Upgrade to Pro for unlimited generation or switch to On-Device Offline Engine.",
            )

        # Consume quota
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.datetime.now(datetime.timezone.utc).isoformat()
            cursor.execute(
                "UPDATE devices SET monthly_usage = monthly_usage + ?, updated_at = ? WHERE device_id = ?",
                (char_count, now, device["device_id"]),
            )
            cursor.execute(
                "INSERT INTO usage_logs (device_id, char_count, voice_id, timestamp) VALUES (?, ?, ?, ?)",
                (device["device_id"], char_count, voice_id, now),
            )
            conn.commit()

        return True, self.get_device_quota(device_id), "ok"

    def redeem_license_key(self, device_id: str, code: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Redeems a Promo / VIP License code for a device.
        Upgrades device to 'pro' tier.
        """
        if not code or not code.strip():
            return False, "License code cannot be empty.", {}

        clean_code = code.strip().upper()
        clean_id = device_id.strip() if device_id else "dev_anonymous"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM license_keys WHERE code = ?", (clean_code,))
            key_row = cursor.fetchone()

            if key_row is None:
                return False, "Invalid promo / license code.", {}

            max_uses = key_row["max_uses"]
            used_count = key_row["used_count"]

            # max_uses == -1 indicates unlimited uses
            if max_uses != -1 and used_count >= max_uses:
                return False, "This promo code has reached its maximum usage limit.", {}

            # Increment used count
            cursor.execute("UPDATE license_keys SET used_count = used_count + 1 WHERE code = ?", (clean_code,))

            # Upgrade device to Pro
            now = datetime.datetime.now(datetime.timezone.utc).isoformat()
            cursor.execute(
                """
                UPDATE devices
                SET tier = 'pro',
                    license_key = ?,
                    note = ?,
                    updated_at = ?
                WHERE device_id = ?
                """,
                (clean_code, f"Redeemed key: {clean_code} ({key_row['note'] or ''})", now, clean_id),
            )
            conn.commit()

        logger.info(f"Device '{clean_id}' successfully upgraded to PRO using code '{clean_code}'")
        return True, "🎉 License activated! You now have lifetime unlimited Kokoro Pro Cloud access.", self.get_device_quota(clean_id)

    def grant_pro(self, device_id: str, tier: str = "pro", note: str = "Admin manual grant") -> Dict[str, Any]:
        """Admin helper: Directly grants Pro status to any device ID."""
        clean_id = device_id.strip()
        self.get_or_create_device(clean_id)
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE devices SET tier = ?, note = ?, updated_at = ? WHERE device_id = ?",
                (tier, note, now, clean_id),
            )
            conn.commit()

        logger.info(f"Admin granted {tier.upper()} status to device '{clean_id}' ({note})")
        return self.get_device_quota(clean_id)

    def create_license_key(
        self, code: str, tier: str = "pro", max_uses: int = 1, note: str = ""
    ) -> Dict[str, Any]:
        """Admin helper: Creates a new promo / VIP key."""
        clean_code = code.strip().upper()
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO license_keys (code, tier, max_uses, used_count, note, created_at)
                VALUES (?, ?, ?, 0, ?, ?)
                """,
                (clean_code, tier, max_uses, note, now),
            )
            conn.commit()

        logger.info(f"Created license key: '{clean_code}' (max_uses={max_uses}, note='{note}')")
        return {
            "code": clean_code,
            "tier": tier,
            "max_uses": max_uses,
            "note": note,
            "created_at": now,
        }

    def list_devices(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Admin helper: List registered devices."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM devices ORDER BY updated_at DESC LIMIT ?", (limit,))
            return [dict(r) for r in cursor.fetchall()]

    def list_license_keys(self) -> List[Dict[str, Any]]:
        """Admin helper: List all promo / license keys."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM license_keys ORDER BY created_at DESC")
            return [dict(r) for r in cursor.fetchall()]

    def reset_device_usage(self, device_id: str) -> Dict[str, Any]:
        """Admin helper: Reset monthly usage for a device."""
        clean_id = device_id.strip()
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE devices SET monthly_usage = 0, updated_at = ? WHERE device_id = ?",
                (now, clean_id),
            )
            conn.commit()
        return self.get_device_quota(clean_id)


# Global singleton database instance
billing_db = BillingDB()
