"""
Kokoro Voice Studio Pro — Billing, Quota & Anonymous Device Management DB
=========================================================================
Persistent SQLite database handling:
  - Anonymous Device ID registry (zero-login)
  - Anti-Uninstall / Anti-Reset protection via Hardware & Network Fingerprinting
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
                    fingerprint TEXT,
                    client_ip TEXT,
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

            # Check if fingerprint / client_ip columns exist in older DBs
            cursor.execute("PRAGMA table_info(devices)")
            columns = [row["name"] for row in cursor.fetchall()]
            if "fingerprint" not in columns:
                cursor.execute("ALTER TABLE devices ADD COLUMN fingerprint TEXT")
            if "client_ip" not in columns:
                cursor.execute("ALTER TABLE devices ADD COLUMN client_ip TEXT")

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
                    client_ip TEXT,
                    timestamp TEXT NOT NULL
                )
                """
            )

            # Check if client_ip column exists in usage_logs in older DBs
            cursor.execute("PRAGMA table_info(usage_logs)")
            log_columns = [row["name"] for row in cursor.fetchall()]
            if "client_ip" not in log_columns:
                cursor.execute("ALTER TABLE usage_logs ADD COLUMN client_ip TEXT")

            conn.commit()

            # Seed default VIP codes if license_keys table is empty
            cursor.execute("SELECT COUNT(*) FROM license_keys")
            count = cursor.fetchone()[0]
            if count == 0:
                now = datetime.datetime.now(datetime.timezone.utc).isoformat()
                default_keys = [
                    ("KOKORO-VIP-LIFETIME", "pro", -1, "Unlimited Lifetime VIP Master Pass", now),
                    ("STUDIO-PRO-UNLIMITED", "pro", -1, "Unlimited Lifetime Studio Pro Pass", now),
                    ("INFINITY-VOICE-PASS", "pro", -1, "Unlimited Lifetime Infinity Pass", now),
                    ("KOKORO-FOUNDER-ACCESS", "pro", -1, "Unlimited Lifetime Founder Pass", now),
                    ("VIP-CREATOR-LIFETIME", "pro", -1, "Unlimited Lifetime Creator Pass", now),
                    ("NEURAL-PRO-FOREVER", "pro", -1, "Unlimited Lifetime Neural Pro Pass", now),
                    ("KOKORO-MASTER-2026", "pro", -1, "Unlimited Lifetime Master Pass 2026", now),
                    ("ULTRA-VOICE-ACCESS", "pro", -1, "Unlimited Lifetime Ultra Voice Pass", now),
                    ("VIP-SPECIAL-GIFT", "pro", -1, "Unlimited Lifetime VIP Gift Pass", now),
                    ("ALPHA-LIFETIME-PASS", "pro", -1, "Unlimited Lifetime Alpha Pass", now),
                ]
                cursor.executemany(
                    "INSERT INTO license_keys (code, tier, max_uses, note, created_at) VALUES (?, ?, ?, ?, ?)",
                    default_keys,
                )
                conn.commit()

    def get_or_create_device(
        self, device_id: str, fingerprint: str = "", client_ip: str = ""
    ) -> Dict[str, Any]:
        """
        Fetch device record or create a fresh profile.
        Includes Anti-Reset protection: if app was uninstalled and reinstalled,
        matches device fingerprint or client IP to retain existing spent characters and Pro status.
        """
        if not device_id or not device_id.strip():
            device_id = "dev_anonymous"

        clean_id = device_id.strip()
        clean_fp = fingerprint.strip() if fingerprint else ""
        clean_ip = client_ip.strip() if client_ip else ""
        current_cycle = self._current_cycle_month()
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM devices WHERE device_id = ?", (clean_id,))
            row = cursor.fetchone()

            if row is not None:
                # Device already exists: update IP and fingerprint if changed
                updates = ["updated_at = ?"]
                params: List[Any] = [now]

                if clean_fp and row["fingerprint"] != clean_fp:
                    updates.append("fingerprint = ?")
                    params.append(clean_fp)
                if clean_ip and row["client_ip"] != clean_ip:
                    updates.append("client_ip = ?")
                    params.append(clean_ip)

                # Monthly cycle reset check
                if row["billing_cycle_month"] != current_cycle:
                    updates.append("monthly_usage = 0")
                    updates.append("billing_cycle_month = ?")
                    params.append(current_cycle)

                params.append(clean_id)
                sql = f"UPDATE devices SET {', '.join(updates)} WHERE device_id = ?"
                cursor.execute(sql, tuple(params))
                conn.commit()

                cursor.execute("SELECT * FROM devices WHERE device_id = ?", (clean_id,))
                return dict(cursor.fetchone())

            # New device ID encountered: Check for Anti-Reset Fingerprint Match
            inherited_tier = "free"
            inherited_usage = 0
            inherited_limit = DEFAULT_FREE_MONTHLY_LIMIT
            inherited_key = None
            note = None
            prev_match = None

            # 1. Match by persistent hardware fingerprint
            if clean_fp:
                cursor.execute(
                    "SELECT * FROM devices WHERE fingerprint = ? AND billing_cycle_month = ? ORDER BY updated_at DESC LIMIT 1",
                    (clean_fp, current_cycle),
                )
                prev_match = cursor.fetchone()
                if prev_match:
                    inherited_tier = prev_match["tier"]
                    inherited_usage = prev_match["monthly_usage"]
                    inherited_limit = prev_match["monthly_limit"]
                    inherited_key = prev_match["license_key"]
                    note = f"Linked via fingerprint to {prev_match['device_id']}"
                    logger.info(f"Anti-Reset match by fingerprint: Device '{clean_id}' inherited {inherited_usage} chars usage / {inherited_tier} tier.")

            # 2. Match by IP address if within current cycle
            if not prev_match and clean_ip and clean_ip not in ("127.0.0.1", "localhost", ""):
                cursor.execute(
                    "SELECT * FROM devices WHERE client_ip = ? AND billing_cycle_month = ? AND monthly_usage > 0 ORDER BY updated_at DESC LIMIT 1",
                    (clean_ip, current_cycle),
                )
                ip_match = cursor.fetchone()
                if ip_match and ip_match["tier"] == "free":
                    inherited_usage = ip_match["monthly_usage"]
                    note = f"Linked via IP to {ip_match['device_id']}"
                    logger.info(f"Anti-Reset match by IP: Device '{clean_id}' inherited {inherited_usage} chars usage.")

            # Insert new device profile with preserved usage
            cursor.execute(
                """
                INSERT INTO devices (
                    device_id, fingerprint, client_ip, tier, monthly_usage, monthly_limit,
                    billing_cycle_month, license_key, note, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    clean_id,
                    clean_fp,
                    clean_ip,
                    inherited_tier,
                    inherited_usage,
                    inherited_limit,
                    current_cycle,
                    inherited_key,
                    note,
                    now,
                    now,
                ),
            )
            conn.commit()

            cursor.execute("SELECT * FROM devices WHERE device_id = ?", (clean_id,))
            return dict(cursor.fetchone())

    def get_device_quota(
        self, device_id: str, fingerprint: str = "", client_ip: str = ""
    ) -> Dict[str, Any]:
        """Returns structured quota information for device."""
        device = self.get_or_create_device(device_id, fingerprint=fingerprint, client_ip=client_ip)
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
        self,
        device_id: str,
        char_count: int,
        voice_id: str = "",
        fingerprint: str = "",
        client_ip: str = "",
    ) -> Tuple[bool, Dict[str, Any], str]:
        """
        Validates whether device has sufficient quota for character length.
        If allowed, records consumption and returns (True, updated_quota, "ok").
        If quota exceeded on free tier, returns (False, quota_info, "quota_exceeded").
        """
        device = self.get_or_create_device(device_id, fingerprint=fingerprint, client_ip=client_ip)
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
                    "INSERT INTO usage_logs (device_id, char_count, voice_id, client_ip, timestamp) VALUES (?, ?, ?, ?, ?)",
                    (device["device_id"], char_count, voice_id, client_ip, now),
                )
                conn.commit()
            return True, self.get_device_quota(device_id, fingerprint, client_ip), "ok"

        # Free tier limit check
        if usage + char_count > limit:
            remaining = max(0, limit - usage)
            return (
                False,
                self.get_device_quota(device_id, fingerprint, client_ip),
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
                "INSERT INTO usage_logs (device_id, char_count, voice_id, client_ip, timestamp) VALUES (?, ?, ?, ?, ?)",
                (device["device_id"], char_count, voice_id, client_ip, now),
            )
            conn.commit()

        return True, self.get_device_quota(device_id, fingerprint, client_ip), "ok"

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
                return False, "This license code has already been redeemed and cannot be reused.", {}

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

    def generate_single_use_batch(
        self, count: int = 10, prefix: str = "KOKORO-PRO", note: str = "1-Time Gift Code"
    ) -> List[Dict[str, Any]]:
        """
        Generates a batch of unique, single-use license keys (max_uses = 1).
        Each key can only be activated by one person/device.
        """
        import secrets

        generated = []
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            for _ in range(count):
                part1 = secrets.token_hex(2).upper()
                part2 = secrets.token_hex(2).upper()
                code = f"{prefix}-{part1}-{part2}"
                
                cursor.execute(
                    """
                    INSERT INTO license_keys (code, tier, max_uses, used_count, note, created_at)
                    VALUES (?, 'pro', 1, 0, ?, ?)
                    """,
                    (code, note, now),
                )
                generated.append({
                    "code": code,
                    "tier": "pro",
                    "max_uses": 1,
                    "used_count": 0,
                    "note": note,
                })
            conn.commit()

        logger.info(f"Generated batch of {count} single-use license codes with prefix '{prefix}'")
        return generated

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
