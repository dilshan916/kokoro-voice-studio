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
            if "cancel_at_period_end" not in columns:
                cursor.execute("ALTER TABLE devices ADD COLUMN cancel_at_period_end INTEGER NOT NULL DEFAULT 0")
            if "subscription_expires_at" not in columns:
                cursor.execute("ALTER TABLE devices ADD COLUMN subscription_expires_at TEXT")

            # Automatic migration: Extract customer & sub IDs from note if not set
            try:
                import re
                cursor.execute("SELECT device_id, note FROM devices WHERE stripe_subscription_id IS NULL AND note LIKE '%Sub: sub_%'")
                for r in cursor.fetchall():
                    d_id = r["device_id"]
                    n_txt = r["note"] or ""
                    c_match = re.search(r"Customer:\s*(cus_[a-zA-Z0-9]+)", n_txt)
                    s_match = re.search(r"Sub:\s*(sub_[a-zA-Z0-9]+)", n_txt)
                    if c_match or s_match:
                        c_val = c_match.group(1) if c_match else None
                        s_val = s_match.group(1) if s_match else None
                        cursor.execute(
                            "UPDATE devices SET stripe_customer_id = COALESCE(?, stripe_customer_id), stripe_subscription_id = COALESCE(?, stripe_subscription_id) WHERE device_id = ?",
                            (c_val, s_val, d_id),
                        )
            except Exception as mig_err:
                logger.warning(f"Note migration warning: {mig_err}")

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

            # 4. API Keys Table (for Paid Developer API & OpenAI compatibility)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS api_keys (
                    key_id TEXT PRIMARY KEY,
                    api_key TEXT UNIQUE NOT NULL,
                    device_id TEXT NOT NULL,
                    name TEXT NOT NULL DEFAULT 'Default API Key',
                    tier TEXT NOT NULL DEFAULT 'free',
                    monthly_usage INTEGER NOT NULL DEFAULT 0,
                    monthly_limit INTEGER NOT NULL DEFAULT 20000,
                    billing_cycle_month TEXT NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    last_used_at TEXT
                )
                """
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_token ON api_keys(api_key)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_device ON api_keys(device_id)")

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

                # Check if prepaid Pro subscription has expired
                row_dict = dict(row)
                if row_dict.get("tier") == "pro" and row_dict.get("subscription_expires_at"):
                    try:
                        exp_str = str(row_dict["subscription_expires_at"]).replace("Z", "+00:00")
                        exp_dt = datetime.datetime.fromisoformat(exp_str)
                        now_dt = datetime.datetime.now(datetime.timezone.utc)
                        if now_dt >= exp_dt:
                            updates.append("tier = 'free'")
                            updates.append("cancel_at_period_end = 0")
                            updates.append("note = 'Subscription expired after 30-day prepaid period'")
                            logger.info(f"Device '{clean_id}' Pro period ended on {exp_dt} -> reverted to free tier")
                    except Exception as ex_err:
                        logger.warning(f"Error checking subscription expiry for {clean_id}: {ex_err}")

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

            # 1. Match by persistent hardware fingerprint (ONLY for the exact same physical phone)
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
                    note = f"Linked via hardware fingerprint to {prev_match['device_id']}"
                    logger.info(f"Anti-Reset match by fingerprint: Device '{clean_id}' inherited {inherited_usage} chars usage / {inherited_tier} tier.")

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

        has_sub = bool(
            device.get("stripe_subscription_id")
            or (device.get("note") and "Sub: sub_" in str(device.get("note")))
        )

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
            "has_subscription": has_sub,
            "cancel_at_period_end": bool(device.get("cancel_at_period_end", 0)),
            "subscription_expires_at": device.get("subscription_expires_at"),
            "stripe_customer_id": device.get("stripe_customer_id"),
            "stripe_subscription_id": device.get("stripe_subscription_id"),
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

    def get_device_raw(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Returns the raw SQLite row dictionary for a device."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM devices WHERE device_id = ?", (device_id.strip(),))
            row = cur.fetchone()
            return dict(row) if row else None

    def grant_pro(
        self,
        device_id: str,
        tier: str = "pro",
        note: str = "Admin manual grant",
        stripe_customer_id: Optional[str] = None,
        stripe_subscription_id: Optional[str] = None,
        cancel_at_period_end: int = 0,
        subscription_expires_at: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Directly grants Pro status to any device ID and stores payment metadata with 30-day expiration."""
        clean_id = device_id.strip()
        self.get_or_create_device(clean_id)
        now_dt = datetime.datetime.now(datetime.timezone.utc)
        now = now_dt.isoformat()

        if not subscription_expires_at:
            # Default to 30 days prepaid period
            subscription_expires_at = (now_dt + datetime.timedelta(days=30)).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE devices 
                SET tier = ?, 
                    note = ?, 
                    stripe_customer_id = COALESCE(?, stripe_customer_id),
                    stripe_subscription_id = COALESCE(?, stripe_subscription_id),
                    cancel_at_period_end = ?,
                    subscription_expires_at = ?,
                    updated_at = ? 
                WHERE device_id = ?
                """,
                (tier, note, stripe_customer_id, stripe_subscription_id, cancel_at_period_end, subscription_expires_at, now, clean_id),
            )
            conn.commit()

        logger.info(f"Updated status for device '{clean_id}': tier={tier}, sub={stripe_subscription_id}, expires_at={subscription_expires_at}")
        return self.get_device_quota(clean_id)

    def update_subscription_renewal(
        self, device_id: str, cancel_at_period_end: bool
    ) -> Dict[str, Any]:
        """
        Toggles whether a subscription auto-renews at the end of the 30-day period.
        Pro status is preserved for the full 30 days regardless of toggle state.
        """
        clean_id = device_id.strip()
        now_dt = datetime.datetime.now(datetime.timezone.utc)
        now = now_dt.isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT subscription_expires_at FROM devices WHERE device_id = ?", (clean_id,))
            row = cursor.fetchone()
            exp_at = row["subscription_expires_at"] if row and row["subscription_expires_at"] else (now_dt + datetime.timedelta(days=30)).isoformat()

            cursor.execute(
                "UPDATE devices SET cancel_at_period_end = ?, subscription_expires_at = ?, updated_at = ? WHERE device_id = ?",
                (1 if cancel_at_period_end else 0, exp_at, now, clean_id),
            )
            conn.commit()
        logger.info(f"Device '{clean_id}' auto-renewal updated: cancel_at_period_end={cancel_at_period_end}, active until {exp_at}")
        return self.get_device_quota(clean_id)

    def cancel_subscription_immediate(
        self, device_id: str, note: str = "Subscription cancelled - retains Pro until period end"
    ) -> Dict[str, Any]:
        """
        Cancels future subscription renewals while strictly preserving Pro features
        until the 30-day prepaid billing period expires. Never wipes features immediately.
        """
        clean_id = device_id.strip()
        now_dt = datetime.datetime.now(datetime.timezone.utc)
        now = now_dt.isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT subscription_expires_at FROM devices WHERE device_id = ?", (clean_id,))
            row = cursor.fetchone()
            exp_at = row["subscription_expires_at"] if row and row["subscription_expires_at"] else (now_dt + datetime.timedelta(days=30)).isoformat()

            cursor.execute(
                """
                UPDATE devices 
                SET cancel_at_period_end = 1,
                    subscription_expires_at = ?,
                    note = ?, 
                    updated_at = ? 
                WHERE device_id = ?
                """,
                (exp_at, note, now, clean_id),
            )
            conn.commit()
        logger.info(f"Device '{clean_id}' subscription cancelled -> retains Pro features until {exp_at}")
        return self.get_device_quota(clean_id)

    def cancel_subscription_by_sub_id(self, subscription_id: str, note: str = "Subscription expired") -> None:
        """
        Syncs subscription cancellation by ID.
        Preserves Pro access if the prepaid 30-day period has not elapsed yet.
        """
        now_dt = datetime.datetime.now(datetime.timezone.utc)
        now = now_dt.isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT device_id, subscription_expires_at FROM devices WHERE stripe_subscription_id = ?", (subscription_id.strip(),))
            rows = cursor.fetchall()
            for r in rows:
                exp_at = r["subscription_expires_at"]
                if exp_at:
                    try:
                        exp_dt = datetime.datetime.fromisoformat(str(exp_at).replace("Z", "+00:00"))
                        if now_dt < exp_dt:
                            cursor.execute(
                                "UPDATE devices SET cancel_at_period_end = 1, note = ?, updated_at = ? WHERE device_id = ?",
                                (f"{note} (retains Pro until {exp_at})", now, r["device_id"]),
                            )
                            continue
                    except Exception:
                        pass
                cursor.execute(
                    "UPDATE devices SET tier = 'free', cancel_at_period_end = 0, note = ?, updated_at = ? WHERE device_id = ?",
                    (note, now, r["device_id"]),
                )
            conn.commit()

    def sync_subscription_status_by_sub_id(self, subscription_id: str, cancel_at_period_end: bool) -> None:
        """Syncs cancel_at_period_end flag from webhook."""
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE devices SET cancel_at_period_end = ?, updated_at = ? WHERE stripe_subscription_id = ?",
                (1 if cancel_at_period_end else 0, now, subscription_id.strip()),
            )
            conn.commit()

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

    # ========================================================================
    # Paid Developer API Key Management & Authentication
    # ========================================================================

    def create_api_key(
        self, device_id: str, name: str = "Default API Key"
    ) -> Dict[str, Any]:
        """
        Generates a new secure API key bound to a device ID.
        Inherits the device's tier and monthly limit.
        """
        import secrets
        clean_id = device_id.strip() if device_id else "dev_anonymous"
        clean_name = name.strip() or "Default API Key"
        key_id = f"key_{secrets.token_hex(6)}"
        token = f"sk_live_kokoro_{secrets.token_hex(16)}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        current_cycle = self._current_cycle_month()

        # Check device tier
        device = self.get_or_create_device(clean_id)
        tier = device.get("tier", "free")
        limit = device.get("monthly_limit", DEFAULT_FREE_MONTHLY_LIMIT)

        # Free tier is restricted to 1 active API key
        if tier != "pro":
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) FROM api_keys WHERE device_id = ? AND is_active = 1",
                    (clean_id,),
                )
                row = cursor.fetchone()
                active_count = row[0] if row else 0
                if active_count >= 1:
                    raise ValueError(
                        "Free plan users are restricted to 1 active API key. "
                        "Please revoke your existing API key or upgrade to Pro to create more."
                    )

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO api_keys (
                    key_id, api_key, device_id, name, tier, monthly_usage,
                    monthly_limit, billing_cycle_month, is_active, created_at
                ) VALUES (?, ?, ?, ?, ?, 0, ?, ?, 1, ?)
                """,
                (key_id, token, clean_id, clean_name, tier, limit, current_cycle, now),
            )
            conn.commit()

        logger.info(f"Created API key {key_id} for device {clean_id} (tier={tier})")
        return {
            "key_id": key_id,
            "api_key": token,
            "name": clean_name,
            "tier": tier,
            "monthly_usage": 0,
            "monthly_limit": limit,
            "is_active": True,
            "created_at": now,
        }

    def list_api_keys(self, device_id: str) -> List[Dict[str, Any]]:
        """List all active API keys for a device ID."""
        clean_id = device_id.strip() if device_id else "dev_anonymous"
        current_cycle = self._current_cycle_month()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Fetch current parent device tier
            cursor.execute("SELECT tier, monthly_limit FROM devices WHERE device_id = ?", (clean_id,))
            dev_row = cursor.fetchone()
            dev_tier = dev_row["tier"] if dev_row else "free"
            dev_limit = -1 if dev_tier == "pro" else (dev_row["monthly_limit"] if dev_row else DEFAULT_FREE_MONTHLY_LIMIT)

            cursor.execute(
                "SELECT * FROM api_keys WHERE device_id = ? AND is_active = 1 ORDER BY created_at DESC",
                (clean_id,),
            )
            rows = cursor.fetchall()
            results = []
            for r in rows:
                k = dict(r)
                k["tier"] = dev_tier
                k["monthly_limit"] = dev_limit
                # Cycle reset check
                if k["billing_cycle_month"] != current_cycle:
                    cursor.execute(
                        "UPDATE api_keys SET monthly_usage = 0, billing_cycle_month = ? WHERE key_id = ?",
                        (current_cycle, k["key_id"]),
                    )
                    k["monthly_usage"] = 0
                    k["billing_cycle_month"] = current_cycle

                raw_key = k["api_key"]
                masked = f"{raw_key[:18]}...{raw_key[-4:]}" if len(raw_key) > 22 else raw_key
                k["masked_key"] = masked
                k["is_active"] = bool(k["is_active"])
                results.append(k)
            conn.commit()
            return results

    def revoke_api_key(self, device_id: str, key_id: str) -> bool:
        """Deactivates an API key."""
        clean_id = device_id.strip() if device_id else "dev_anonymous"
        clean_kid = key_id.strip()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE api_keys SET is_active = 0 WHERE key_id = ? AND device_id = ?",
                (clean_kid, clean_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def authenticate_api_key(self, api_key: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """
        Validates API key token.
        Returns (is_valid, key_dict, error_message).
        """
        if not api_key or not api_key.strip():
            return False, None, "Missing API key in Authorization header"

        clean_token = api_key.strip()
        current_cycle = self._current_cycle_month()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM api_keys WHERE api_key = ? AND is_active = 1",
                (clean_token,),
            )
            row = cursor.fetchone()
            if not row:
                return False, None, "Invalid or revoked API key"

            key_dict = dict(row)
            # Cycle reset check
            if key_dict["billing_cycle_month"] != current_cycle:
                cursor.execute(
                    "UPDATE api_keys SET monthly_usage = 0, billing_cycle_month = ? WHERE key_id = ?",
                    (current_cycle, key_dict["key_id"]),
                )
                conn.commit()
                key_dict["monthly_usage"] = 0
                key_dict["billing_cycle_month"] = current_cycle

            # Sync key tier dynamically with parent device's current tier
            cursor.execute("SELECT tier, monthly_limit FROM devices WHERE device_id = ?", (key_dict["device_id"],))
            dev_row = cursor.fetchone()
            if dev_row:
                dev_tier = dev_row["tier"]
                key_dict["tier"] = dev_tier
                if dev_tier == "pro":
                    key_dict["monthly_limit"] = -1
                else:
                    key_dict["monthly_limit"] = dev_row["monthly_limit"]

            return True, key_dict, "OK"

    def check_and_consume_api_key_quota(
        self, api_key: str, char_count: int, client_ip: str = "", voice_id: str = ""
    ) -> Tuple[bool, Dict[str, Any], str]:
        """
        Deducts characters from the API key's quota.
        """
        is_valid, key_data, err = self.authenticate_api_key(api_key)
        if not is_valid or not key_data:
            return False, {}, err

        tier = key_data["tier"]
        usage = key_data["monthly_usage"]
        limit = key_data["monthly_limit"]
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Pro / Unlimited checks
        if tier == "pro" or limit < 0:
            new_usage = usage + char_count
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE api_keys SET monthly_usage = ?, last_used_at = ? WHERE key_id = ?",
                    (new_usage, now, key_data["key_id"]),
                )
                cursor.execute(
                    "INSERT INTO usage_logs (device_id, char_count, voice_id, client_ip, timestamp) VALUES (?, ?, ?, ?, ?)",
                    (f"api:{key_data['key_id']}", char_count, voice_id, client_ip, now),
                )
                conn.commit()

            return True, {
                "tier": "pro",
                "monthly_usage": new_usage,
                "monthly_limit": -1,
                "remaining_chars": "unlimited",
            }, "OK"

        # Quota check for free/metered tier
        if usage + char_count > limit:
            remaining = max(0, limit - usage)
            return False, {
                "tier": tier,
                "monthly_usage": usage,
                "monthly_limit": limit,
                "remaining_chars": remaining,
            }, f"Monthly API character quota exceeded ({usage:,}/{limit:,}). Please upgrade or top up credits."

        new_usage = usage + char_count
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE api_keys SET monthly_usage = ?, last_used_at = ? WHERE key_id = ?",
                (new_usage, now, key_data["key_id"]),
            )
            cursor.execute(
                "INSERT INTO usage_logs (device_id, char_count, voice_id, client_ip, timestamp) VALUES (?, ?, ?, ?, ?)",
                (f"api:{key_data['key_id']}", char_count, voice_id, client_ip, now),
            )
            conn.commit()

        return True, {
            "tier": tier,
            "monthly_usage": new_usage,
            "monthly_limit": limit,
            "remaining_chars": max(0, limit - new_usage),
        }, "OK"


# Global singleton database instance
billing_db = BillingDB()

