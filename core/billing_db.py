"""
Kokoro Voice Studio Pro — Billing, Quota & Anonymous Device Management DB
=========================================================================
Persistent SQLite database handling:
  - Cryptographically verified anonymous device sessions (zero-login)
  - SHA-256 hashed Developer API keys (zero plaintext storage at rest)
  - Account recovery via high-entropy recovery keys
  - 30,000 characters/month Free Tier enforcement
  - Pro Plan (Unlimited) tier management
  - Promo / VIP License key validation with brute-force lockout
  - Stripe Customer & Subscription metadata binding
  - Audio artifact ownership verification & TTL lifecycle
  - Long-form TTS asynchronous background job queues
"""

from __future__ import annotations

import datetime
import hashlib
import logging
import os
import secrets
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("kokoro.billing")

DEFAULT_FREE_MONTHLY_LIMIT = 30000
MAX_FAILED_LICENSE_ATTEMPTS = 5
LICENSE_LOCKOUT_WINDOW_SECONDS = 900.0  # 15 minutes
MAX_SESSIONS_PER_IP_PER_DAY = 3
SESSION_CREATION_WINDOW_SECONDS = 86400.0  # 24 hours
DEFAULT_ARTIFACT_TTL_SECONDS = 7200  # 2 hours
DEFAULT_JOB_TTL_SECONDS = 14400  # 4 hours


class BillingDB:
    """Manages SQLite storage for anonymous device quotas, sessions, and license keys."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            base_dir = Path(__file__).resolve().parent.parent
            data_dir = base_dir / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = str(data_dir / "billing.db")
        else:
            self.db_path = db_path

        # In-memory velocity & brute-force trackers
        self._failed_license_attempts: Dict[str, List[float]] = {}
        self._session_creations_by_ip: Dict[str, List[float]] = {}

        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _current_cycle_month(self) -> str:
        """Returns current year-month string: 'YYYY-MM' (e.g. '2026-09')"""
        return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m")

    def _init_db(self) -> None:
        """Create tables and indexes if they do not already exist, and perform safe migrations."""
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
                    monthly_limit INTEGER NOT NULL DEFAULT 30000,
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

            # Check if columns exist in older DBs
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
            if "recovery_key_hash" not in columns:
                cursor.execute("ALTER TABLE devices ADD COLUMN recovery_key_hash TEXT")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_devices_recovery ON devices(recovery_key_hash)")

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

            # 2. Device Sessions Table (Cryptographic Anonymous Session Layer)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS device_sessions (
                    session_id TEXT PRIMARY KEY,
                    device_id TEXT NOT NULL,
                    token_hash TEXT UNIQUE NOT NULL,
                    client_ip TEXT,
                    user_agent TEXT,
                    created_at TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    is_revoked INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY(device_id) REFERENCES devices(device_id) ON DELETE CASCADE
                )
                """
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_token_hash ON device_sessions(token_hash)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_device ON device_sessions(device_id)")

            # 3. License / Promo Keys Table
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

            # 4. Usage Log Table (for analytics / auditing)
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
            cursor.execute("PRAGMA table_info(usage_logs)")
            log_columns = [row["name"] for row in cursor.fetchall()]
            if "client_ip" not in log_columns:
                cursor.execute("ALTER TABLE usage_logs ADD COLUMN client_ip TEXT")

            # 5. API Keys Table (Hashed at rest)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS api_keys (
                    key_id TEXT PRIMARY KEY,
                    api_key_hash TEXT UNIQUE NOT NULL,
                    masked_key TEXT NOT NULL,
                    device_id TEXT NOT NULL,
                    name TEXT NOT NULL DEFAULT 'Default API Key',
                    tier TEXT NOT NULL DEFAULT 'free',
                    monthly_usage INTEGER NOT NULL DEFAULT 0,
                    monthly_limit INTEGER NOT NULL DEFAULT 30000,
                    billing_cycle_month TEXT NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    last_used_at TEXT
                )
                """
            )

            cursor.execute("PRAGMA table_info(api_keys)")
            ak_columns = [row["name"] for row in cursor.fetchall()]

            # CRITICAL SECURITY MIGRATION:
            # If legacy plaintext column 'api_key' exists, migrate to hashed table schema
            if "api_key" in ak_columns:
                try:
                    cursor.execute("SELECT key_id, api_key, device_id, name, tier, monthly_usage, monthly_limit, billing_cycle_month, is_active, created_at, last_used_at FROM api_keys")
                    legacy_keys = cursor.fetchall()
                    cursor.execute(
                        """
                        CREATE TABLE IF NOT EXISTS api_keys_new (
                            key_id TEXT PRIMARY KEY,
                            api_key_hash TEXT UNIQUE NOT NULL,
                            masked_key TEXT NOT NULL,
                            device_id TEXT NOT NULL,
                            name TEXT NOT NULL DEFAULT 'Default API Key',
                            tier TEXT NOT NULL DEFAULT 'free',
                            monthly_usage INTEGER NOT NULL DEFAULT 0,
                            monthly_limit INTEGER NOT NULL DEFAULT 30000,
                            billing_cycle_month TEXT NOT NULL,
                            is_active INTEGER NOT NULL DEFAULT 1,
                            created_at TEXT NOT NULL,
                            last_used_at TEXT
                        )
                        """
                    )
                    for lk in legacy_keys:
                        k_id = lk["key_id"]
                        raw_val = (lk["api_key"] or "").strip()
                        if raw_val:
                            h_val = hashlib.sha256(raw_val.encode("utf-8")).hexdigest()
                            m_val = f"{raw_val[:18]}...{raw_val[-4:]}" if len(raw_val) > 22 else raw_val
                        else:
                            # Already hashed in previous attempt
                            h_val = lk.get("api_key_hash") or hashlib.sha256(k_id.encode("utf-8")).hexdigest()
                            m_val = lk.get("masked_key") or "sk_live_...migrated"

                        cursor.execute(
                            """
                            INSERT OR REPLACE INTO api_keys_new (
                                key_id, api_key_hash, masked_key, device_id, name, tier,
                                monthly_usage, monthly_limit, billing_cycle_month, is_active, created_at, last_used_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (k_id, h_val, m_val, lk["device_id"], lk["name"], lk["tier"],
                             lk["monthly_usage"], lk["monthly_limit"], lk["billing_cycle_month"],
                             lk["is_active"], lk["created_at"], lk["last_used_at"]),
                        )
                    cursor.execute("DROP TABLE api_keys")
                    cursor.execute("ALTER TABLE api_keys_new RENAME TO api_keys")
                    logger.info(f"Security Migration: Successfully migrated {len(legacy_keys)} API keys to hash-only table and dropped plaintext column.")
                except Exception as ak_mig_err:
                    logger.warning(f"API key migration warning: {ak_mig_err}")

            cursor.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(api_key_hash)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_device ON api_keys(device_id)")

            # 6. Audio Artifacts Table (Ownership and 2-hour TTL retention)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS audio_artifacts (
                    file_id TEXT PRIMARY KEY,
                    device_id TEXT NOT NULL,
                    filename TEXT UNIQUE NOT NULL,
                    format TEXT NOT NULL DEFAULT 'wav',
                    file_size INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    FOREIGN KEY(device_id) REFERENCES devices(device_id)
                )
                """
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_artifacts_filename ON audio_artifacts(filename)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_artifacts_device ON audio_artifacts(device_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_artifacts_expires ON audio_artifacts(expires_at)")

            # 7. Asynchronous TTS Jobs Table (Long-form Pro batch rendering)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS tts_jobs (
                    job_id TEXT PRIMARY KEY,
                    device_id TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'queued',
                    text_length INTEGER NOT NULL,
                    voice_id TEXT NOT NULL,
                    speed REAL NOT NULL DEFAULT 1.0,
                    eq_preset TEXT NOT NULL DEFAULT 'Clean Studio (Default)',
                    lang TEXT NOT NULL DEFAULT 'auto',
                    output_format TEXT NOT NULL DEFAULT 'wav',
                    audio_url TEXT,
                    filename TEXT,
                    duration REAL,
                    file_size_bytes INTEGER,
                    error_message TEXT,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    expires_at TEXT NOT NULL,
                    FOREIGN KEY(device_id) REFERENCES devices(device_id)
                )
                """
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tts_jobs_device ON tts_jobs(device_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tts_jobs_status ON tts_jobs(status)")

            # Automatic migration: bump legacy limits
            try:
                cursor.execute("UPDATE devices SET monthly_limit = 30000 WHERE tier = 'free' AND monthly_limit = 20000")
                cursor.execute("UPDATE api_keys SET monthly_limit = 30000 WHERE tier = 'free' AND monthly_limit = 20000")
            except Exception as mig_lim_err:
                logger.warning(f"Limit migration warning: {mig_lim_err}")

            conn.commit()

    # ========================================================================
    # Anonymous Session Authentication (Zero-Login Security Layer)
    # ========================================================================

    def can_create_device_session(self, client_ip: str) -> bool:
        """
        Anti-Abuse Layer 2: Checks if client IP has exceeded max allowed anonymous sessions per 24 hours.
        Prevents automated bot cycling without restricting standard browser visitors.
        """
        if not client_ip:
            return True

        now = time.time()
        cutoff = now - SESSION_CREATION_WINDOW_SECONDS

        timestamps = self._session_creations_by_ip.get(client_ip, [])
        timestamps = [t for t in timestamps if t > cutoff]
        self._session_creations_by_ip[client_ip] = timestamps

        return len(timestamps) < MAX_SESSIONS_PER_IP_PER_DAY

    def record_session_creation(self, client_ip: str) -> None:
        """Records an anonymous session creation event for velocity tracking."""
        if not client_ip:
            return
        now = time.time()
        if client_ip not in self._session_creations_by_ip:
            self._session_creations_by_ip[client_ip] = []
        self._session_creations_by_ip[client_ip].append(now)

    def create_device_session(
        self, device_id: Optional[str] = None, client_ip: str = "", user_agent: str = ""
    ) -> Tuple[str, str, Dict[str, Any]]:
        """
        Issues an authoritative server-side anonymous session token.
        Returns (session_id, raw_session_token, device_quota_info).
        """
        clean_ip = client_ip.strip() if client_ip else ""
        clean_ua = user_agent[:250].strip() if user_agent else ""

        # If no device_id provided, generate a fresh random device identity
        if not device_id or not device_id.strip():
            device_id = f"dev_web_{secrets.token_hex(8)}"
            self.record_session_creation(clean_ip)

        clean_id = device_id.strip()
        self.get_or_create_device(clean_id, client_ip=clean_ip)

        session_id = f"sess_{secrets.token_hex(12)}"
        raw_token = secrets.token_urlsafe(32)  # 256 bits of entropy
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

        now_dt = datetime.datetime.now(datetime.timezone.utc)
        now = now_dt.isoformat()
        expires_at = (now_dt + datetime.timedelta(days=365)).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO device_sessions (
                    session_id, device_id, token_hash, client_ip, user_agent,
                    created_at, last_seen_at, expires_at, is_revoked
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
                """,
                (session_id, clean_id, token_hash, clean_ip, clean_ua, now, now, expires_at),
            )
            conn.commit()

        logger.info(f"Created secure anonymous session {session_id} for device '{clean_id}'")
        return session_id, raw_token, self.get_device_quota(clean_id)

    def authenticate_session(
        self, raw_token: str
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Validates the presentation of a session token.
        Returns (is_valid, device_id, session_record).
        """
        if not raw_token or not raw_token.strip():
            return False, None, None

        token_hash = hashlib.sha256(raw_token.strip().encode("utf-8")).hexdigest()
        now_dt = datetime.datetime.now(datetime.timezone.utc)
        now = now_dt.isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM device_sessions 
                WHERE token_hash = ? AND is_revoked = 0
                """,
                (token_hash,),
            )
            row = cursor.fetchone()
            if not row:
                return False, None, None

            session = dict(row)
            # Expiration check
            try:
                exp_dt = datetime.datetime.fromisoformat(str(session["expires_at"]).replace("Z", "+00:00"))
                if now_dt >= exp_dt:
                    return False, None, None
            except Exception:
                pass

            # Update last_seen_at (sliding window)
            cursor.execute(
                "UPDATE device_sessions SET last_seen_at = ? WHERE session_id = ?",
                (now, session["session_id"]),
            )
            conn.commit()

            return True, session["device_id"], session

    def revoke_session(self, raw_token: str) -> bool:
        """Revokes an active session token."""
        if not raw_token:
            return False
        token_hash = hashlib.sha256(raw_token.strip().encode("utf-8")).hexdigest()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE device_sessions SET is_revoked = 1 WHERE token_hash = ?", (token_hash,))
            conn.commit()
            return cursor.rowcount > 0

    # ========================================================================
    # Pro Account Restoration & Recovery Key Management
    # ========================================================================

    def generate_recovery_key(self, device_id: str) -> str:
        """
        Generates a 192-bit cryptographically random recovery key for a Pro account.
        Stores SHA-256 hash in SQLite; returns raw secret string to display ONCE to user.
        """
        clean_id = device_id.strip()
        raw_key = f"sayrec_{secrets.token_urlsafe(24)}"
        key_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE devices SET recovery_key_hash = ? WHERE device_id = ?",
                (key_hash, clean_id),
            )
            conn.commit()

        logger.info(f"Generated recovery key hash for device '{clean_id}'")
        return raw_key

    def recover_account(
        self, recovery_key: str, client_ip: str = "", user_agent: str = ""
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Restores access to an existing account using a verified recovery key.
        Revokes old sessions and issues a new session for the recovered account.
        """
        if not recovery_key or not recovery_key.strip():
            return False, "Recovery key cannot be empty.", None

        clean_key = recovery_key.strip()
        key_hash = hashlib.sha256(clean_key.encode("utf-8")).hexdigest()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT device_id, tier FROM devices WHERE recovery_key_hash = ?", (key_hash,))
            row = cursor.fetchone()
            if not row:
                return False, "Invalid or unrecognized recovery key.", None

            target_device = row["device_id"]

            # Revoke all previous sessions for this device to prevent session hijacking
            cursor.execute("UPDATE device_sessions SET is_revoked = 1 WHERE device_id = ?", (target_device,))
            conn.commit()

        # Issue new session for this device
        session_id, raw_token, quota_info = self.create_device_session(
            device_id=target_device, client_ip=client_ip, user_agent=user_agent
        )

        logger.info(f"Account '{target_device}' successfully recovered via recovery key from IP {client_ip}")
        return True, "Account successfully restored!", {
            "device_id": target_device,
            "session_token": raw_token,
            "quota": quota_info,
        }

    # ========================================================================
    # Core Device Quota & Identity Storage
    # ========================================================================

    def get_or_create_device(
        self, device_id: str, fingerprint: str = "", client_ip: str = ""
    ) -> Dict[str, Any]:
        """Fetch device record or create a fresh profile."""
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

            # Create new device profile
            cursor.execute(
                """
                INSERT INTO devices (
                    device_id, fingerprint, client_ip, tier, monthly_usage, monthly_limit,
                    billing_cycle_month, created_at, updated_at
                ) VALUES (?, ?, ?, 'free', 0, ?, ?, ?, ?)
                """,
                (clean_id, clean_fp, clean_ip, DEFAULT_FREE_MONTHLY_LIMIT, current_cycle, now, now),
            )
            conn.commit()

            cursor.execute("SELECT * FROM devices WHERE device_id = ?", (clean_id,))
            return dict(cursor.fetchone())

    def get_device_quota(
        self, device_id: str, fingerprint: str = "", client_ip: str = ""
    ) -> Dict[str, Any]:
        """
        Returns sanitized quota information.
        CRITICAL: Never exposes stripe_customer_id, stripe_subscription_id, license_key, or internal note.
        """
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
            "has_subscription": has_sub,
            "cancel_at_period_end": bool(device.get("cancel_at_period_end", 0)),
            "subscription_expires_at": device.get("subscription_expires_at"),
        }

    def check_and_consume_quota(
        self,
        device_id: str,
        char_count: int,
        voice_id: str = "",
        fingerprint: str = "",
        client_ip: str = "",
    ) -> Tuple[bool, Dict[str, Any], str]:
        """Validates quota and records character usage."""
        device = self.get_or_create_device(device_id, fingerprint=fingerprint, client_ip=client_ip)
        tier = device.get("tier", "free")
        usage = device.get("monthly_usage", 0)
        limit = device.get("monthly_limit", DEFAULT_FREE_MONTHLY_LIMIT)

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

        if usage + char_count > limit:
            remaining = max(0, limit - usage)
            return (
                False,
                self.get_device_quota(device_id, fingerprint, client_ip),
                f"Monthly free Cloud quota exceeded ({usage:,} / {limit:,} chars used). Remaining: {remaining:,} chars. Upgrade to Pro for unlimited generation.",
            )

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

    # ========================================================================
    # License Keys & Brute-Force Defense
    # ========================================================================

    def is_license_attempt_locked(self, client_ip: str) -> bool:
        """Checks if client IP is currently locked out from license redemption attempts."""
        if not client_ip:
            return False
        now = time.time()
        cutoff = now - LICENSE_LOCKOUT_WINDOW_SECONDS
        attempts = self._failed_license_attempts.get(client_ip, [])
        attempts = [t for t in attempts if t > cutoff]
        self._failed_license_attempts[client_ip] = attempts
        return len(attempts) >= MAX_FAILED_LICENSE_ATTEMPTS

    def record_failed_license_attempt(self, client_ip: str) -> None:
        """Records an invalid license redemption attempt."""
        if not client_ip:
            return
        now = time.time()
        if client_ip not in self._failed_license_attempts:
            self._failed_license_attempts[client_ip] = []
        self._failed_license_attempts[client_ip].append(now)

    def redeem_license_key(
        self, device_id: str, code: str, client_ip: str = ""
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Redeems a Promo / VIP License code for an authenticated device.
        Enforces 5-attempt/15-min IP rate limiting and constant-time matching.
        """
        if self.is_license_attempt_locked(client_ip):
            return (
                False,
                "Too many failed redemption attempts. Access temporarily locked for 15 minutes.",
                {},
            )

        if not code or not code.strip():
            return False, "License code cannot be empty.", {}

        clean_code = code.strip().upper()
        clean_id = device_id.strip() if device_id else "dev_anonymous"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM license_keys WHERE code = ?", (clean_code,))
            key_row = cursor.fetchone()

            if key_row is None or not secrets.compare_digest(key_row["code"], clean_code):
                self.record_failed_license_attempt(client_ip)
                return False, "Invalid or expired promo / license code.", {}

            max_uses = key_row["max_uses"]
            used_count = key_row["used_count"]

            if max_uses != -1 and used_count >= max_uses:
                self.record_failed_license_attempt(client_ip)
                return False, "This license code has already reached its redemption limit.", {}

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

        # Reset failed attempts for this IP on success
        self._failed_license_attempts.pop(client_ip, None)

        # Generate a recovery key so the user can restore Pro if they switch devices
        recovery_key = self.generate_recovery_key(clean_id)
        quota_data = self.get_device_quota(clean_id)
        quota_data["recovery_key"] = recovery_key

        logger.info(f"Device '{clean_id}' successfully upgraded to PRO using code '{clean_code}'")
        return True, "🎉 License activated! You now have lifetime unlimited Kokoro Pro Cloud access.", quota_data

    def generate_single_use_batch(
        self, count: int = 10, prefix: str = "KOKORO-PRO", note: str = "1-Time Gift Code"
    ) -> List[Dict[str, Any]]:
        """
        Generates unique, single-use license keys with 128-bit cryptographic entropy.
        """
        generated = []
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            for _ in range(count):
                token_hex = secrets.token_hex(16).upper()  # 128 bits of entropy
                code = f"{prefix}-{token_hex[:4]}-{token_hex[4:8]}-{token_hex[8:12]}-{token_hex[12:16]}"
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

        logger.info(f"Generated batch of {count} 128-bit license codes with prefix '{prefix}'")
        return generated

    def create_license_key(
        self, code: str, tier: str = "pro", max_uses: int = 1, note: str = ""
    ) -> Dict[str, Any]:
        """Admin helper: Creates a custom promo / VIP key."""
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

        return {
            "code": clean_code,
            "tier": tier,
            "max_uses": max_uses,
            "note": note,
            "created_at": now,
        }

    # ========================================================================
    # Developer API Key Management (SHA-256 Hashed at Rest)
    # ========================================================================

    def create_api_key(
        self, device_id: str, name: str = "Default API Key"
    ) -> Dict[str, Any]:
        """
        Generates a new secure API key bound to a device ID.
        Stores SHA-256 hash at rest; returns raw token string ONCE upon creation.
        """
        clean_id = device_id.strip() if device_id else "dev_anonymous"
        clean_name = name.strip() or "Default API Key"
        key_id = f"key_{secrets.token_hex(6)}"
        token = f"sk_live_kokoro_{secrets.token_hex(16)}"  # 128-bit token
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        masked = f"{token[:18]}...{token[-4:]}"

        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        current_cycle = self._current_cycle_month()

        device = self.get_or_create_device(clean_id)
        tier = device.get("tier", "free")
        limit = device.get("monthly_limit", DEFAULT_FREE_MONTHLY_LIMIT)

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
                    key_id, api_key_hash, masked_key, device_id, name, tier,
                    monthly_usage, monthly_limit, billing_cycle_month, is_active, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, 1, ?)
                """,
                (key_id, token_hash, masked, clean_id, clean_name, tier, limit, current_cycle, now),
            )
            conn.commit()

        logger.info(f"Created hashed API key {key_id} for device {clean_id} (tier={tier})")
        return {
            "key_id": key_id,
            "api_key": token,  # Displayed ONCE to user
            "raw_key": token,  # Normalized alias
            "masked_key": masked,
            "name": clean_name,
            "tier": tier,
            "monthly_usage": 0,
            "monthly_limit": limit,
            "is_active": True,
            "created_at": now,
        }

    def list_api_keys(self, device_id: str) -> List[Dict[str, Any]]:
        """
        List all active API keys for a device ID.
        CRITICAL FIX: Never returns raw api_key or api_key_hash.
        """
        clean_id = device_id.strip() if device_id else "dev_anonymous"
        current_cycle = self._current_cycle_month()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT tier, monthly_limit FROM devices WHERE device_id = ?", (clean_id,))
            dev_row = cursor.fetchone()
            dev_tier = dev_row["tier"] if dev_row else "free"
            dev_limit = -1 if dev_tier == "pro" else (dev_row["monthly_limit"] if dev_row else DEFAULT_FREE_MONTHLY_LIMIT)

            cursor.execute(
                """
                SELECT key_id, name, masked_key, tier, monthly_usage, monthly_limit,
                       billing_cycle_month, is_active, created_at, last_used_at
                FROM api_keys 
                WHERE device_id = ? AND is_active = 1 
                ORDER BY created_at DESC
                """,
                (clean_id,),
            )
            rows = cursor.fetchall()
            results = []
            for r in rows:
                k = dict(r)
                k["tier"] = dev_tier
                k["monthly_limit"] = dev_limit

                if k["billing_cycle_month"] != current_cycle:
                    cursor.execute(
                        "UPDATE api_keys SET monthly_usage = 0, billing_cycle_month = ? WHERE key_id = ?",
                        (current_cycle, k["key_id"]),
                    )
                    k["monthly_usage"] = 0
                    k["billing_cycle_month"] = current_cycle

                k["is_active"] = bool(k["is_active"])
                results.append(k)
            conn.commit()
            return results

    def revoke_api_key(self, device_id: str, key_id: str) -> bool:
        """Deactivates an API key enforcing device ownership."""
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
        Validates API key token by matching its SHA-256 hash.
        Returns (is_valid, key_dict, error_message).
        """
        if not api_key or not api_key.strip():
            return False, None, "Missing API key in Authorization header"

        clean_token = api_key.strip()
        token_hash = hashlib.sha256(clean_token.encode("utf-8")).hexdigest()
        current_cycle = self._current_cycle_month()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM api_keys WHERE api_key_hash = ? AND is_active = 1",
                (token_hash,),
            )
            row = cursor.fetchone()
            if not row:
                return False, None, "Invalid or revoked API key"

            key_dict = dict(row)
            if key_dict["billing_cycle_month"] != current_cycle:
                cursor.execute(
                    "UPDATE api_keys SET monthly_usage = 0, billing_cycle_month = ? WHERE key_id = ?",
                    (current_cycle, key_dict["key_id"]),
                )
                conn.commit()
                key_dict["monthly_usage"] = 0
                key_dict["billing_cycle_month"] = current_cycle

            # Sync tier dynamically with parent device
            cursor.execute("SELECT tier, monthly_limit FROM devices WHERE device_id = ?", (key_dict["device_id"],))
            dev_row = cursor.fetchone()
            if dev_row:
                dev_tier = dev_row["tier"]
                key_dict["tier"] = dev_tier
                key_dict["monthly_limit"] = -1 if dev_tier == "pro" else dev_row["monthly_limit"]

            return True, key_dict, "OK"

    def check_and_consume_api_key_quota(
        self, api_key: str, char_count: int, client_ip: str = "", voice_id: str = ""
    ) -> Tuple[bool, Dict[str, Any], str]:
        """Deducts characters from the API key's quota."""
        is_valid, key_data, err = self.authenticate_api_key(api_key)
        if not is_valid or not key_data:
            return False, {}, err

        tier = key_data["tier"]
        usage = key_data["monthly_usage"]
        limit = key_data["monthly_limit"]
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

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

        if usage + char_count > limit:
            remaining = max(0, limit - usage)
            return False, {
                "tier": tier,
                "monthly_usage": usage,
                "monthly_limit": limit,
                "remaining_chars": remaining,
            }, f"Monthly API character quota exceeded ({usage:,}/{limit:,}). Please upgrade to Pro."

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

    # ========================================================================
    # Audio Artifacts & Retention Policy (2-Hour TTL)
    # ========================================================================

    def record_audio_artifact(
        self,
        device_id: str,
        filename: str,
        format: str = "wav",
        file_size: int = 0,
        ttl_seconds: int = DEFAULT_ARTIFACT_TTL_SECONDS,
        file_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Registers a generated audio artifact with ownership and expiration timestamp."""
        if not file_id:
            file_id = f"art_{secrets.token_hex(8)}"
        now_dt = datetime.datetime.now(datetime.timezone.utc)
        now = now_dt.isoformat()
        expires_at = (now_dt + datetime.timedelta(seconds=ttl_seconds)).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO audio_artifacts (
                    file_id, device_id, filename, format, file_size, created_at, expires_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (file_id, device_id, filename, format, file_size, now, expires_at),
            )
            conn.commit()

        return {
            "file_id": file_id,
            "device_id": device_id,
            "filename": filename,
            "format": format,
            "file_size": file_size,
            "created_at": now,
            "expires_at": expires_at,
        }

    # Alias for backward compatibility
    create_audio_artifact = record_audio_artifact

    def get_audio_artifact(
        self, filename: str, device_id: Optional[str] = None
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        Verifies artifact access and ownership.
        Returns ("OK", data), ("UNAUTHORIZED", None), or ("NOT_FOUND", None).
        """
        clean_fn = Path(filename).name
        now_dt = datetime.datetime.now(datetime.timezone.utc)

        stem = Path(clean_fn).stem
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM audio_artifacts WHERE filename = ? OR filename LIKE ? ORDER BY created_at DESC LIMIT 1",
                (clean_fn, f"{stem}.%"),
            )
            row = cursor.fetchone()
            if not row:
                return "NOT_FOUND", None

            data = dict(row)
            try:
                exp_dt = datetime.datetime.fromisoformat(str(data["expires_at"]).replace("Z", "+00:00"))
                if now_dt >= exp_dt:
                    return "EXPIRED", None
            except Exception:
                pass

            if not device_id or data["device_id"] != device_id:
                return "UNAUTHORIZED", None

            return "OK", data

    def cleanup_expired_artifacts(self, output_dir: Path, max_age_seconds: int = 7200) -> int:
        """
        Application-aware cleanup task: Prunes expired audio artifacts and unlinks files.
        Ignores files modified in the last 15 minutes to avoid race conditions with active downloads.
        """
        now_dt = datetime.datetime.now(datetime.timezone.utc)
        now = now_dt.isoformat()
        cleaned_count = 0
        safety_cutoff = time.time() - 900  # 15 minutes grace period

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM audio_artifacts WHERE expires_at < ?", (now,))
            expired_rows = cursor.fetchall()

            for r in expired_rows:
                fname = r["filename"]
                fpath = output_dir / fname
                try:
                    if fpath.exists() and fpath.stat().st_mtime < safety_cutoff:
                        fpath.unlink(missing_ok=True)
                        cleaned_count += 1
                    # Also clean matching subtitle file if present
                    srt_name = f"{fpath.stem}.srt"
                    srt_path = output_dir / srt_name
                    if srt_path.exists() and srt_path.stat().st_mtime < safety_cutoff:
                        srt_path.unlink(missing_ok=True)
                except Exception as e:
                    logger.warning(f"Error unlinking expired artifact {fname}: {e}")

            cursor.execute("DELETE FROM audio_artifacts WHERE expires_at < ?", (now,))
            conn.commit()

        return cleaned_count

    # ========================================================================
    # Asynchronous TTS Jobs (Long-Form Pro Audio Rendering)
    # ========================================================================

    def create_tts_job(
        self,
        device_id: str,
        text_length: int,
        voice_id: str,
        speed: float = 1.0,
        eq_preset: str = "Clean Studio (Default)",
        lang: str = "auto",
        output_format: str = "wav",
        ttl_seconds: int = DEFAULT_JOB_TTL_SECONDS,
    ) -> Dict[str, Any]:
        """Enqueues an asynchronous long-form rendering job."""
        job_id = f"job_{secrets.token_hex(12)}"
        now_dt = datetime.datetime.now(datetime.timezone.utc)
        now = now_dt.isoformat()
        expires_at = (now_dt + datetime.timedelta(seconds=ttl_seconds)).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO tts_jobs (
                    job_id, device_id, status, text_length, voice_id, speed,
                    eq_preset, lang, output_format, created_at, expires_at
                ) VALUES (?, ?, 'queued', ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (job_id, device_id, text_length, voice_id, speed, eq_preset, lang, output_format, now, expires_at),
            )
            conn.commit()

        return {
            "job_id": job_id,
            "device_id": device_id,
            "status": "queued",
            "text_length": text_length,
            "voice_id": voice_id,
            "created_at": now,
            "expires_at": expires_at,
        }

    def get_tts_job(
        self, job_id: str, device_id: Optional[str] = None
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        Retrieves job status enforcing session ownership.
        Returns ("OK", job), ("UNAUTHORIZED", None), or ("NOT_FOUND", None).
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tts_jobs WHERE job_id = ?", (job_id.strip(),))
            row = cursor.fetchone()
            if not row:
                return "NOT_FOUND", None

            data = dict(row)
            if device_id and data["device_id"] != device_id:
                return "UNAUTHORIZED", None

            return "OK", data

    def update_tts_job(
        self,
        job_id: str,
        status: Optional[str] = None,
        audio_url: Optional[str] = None,
        filename: Optional[str] = None,
        duration: Optional[float] = None,
        file_size_bytes: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Updates job progress, execution timestamps, and final artifact link."""
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        updates = []
        params: List[Any] = []

        if status:
            updates.append("status = ?")
            params.append(status)
            if status == "processing":
                updates.append("started_at = ?")
                params.append(now)
            elif status in ("completed", "failed", "cancelled"):
                updates.append("completed_at = ?")
                params.append(now)

        if audio_url:
            updates.append("audio_url = ?")
            params.append(audio_url)
        if filename:
            updates.append("filename = ?")
            params.append(filename)
        if duration is not None:
            updates.append("duration = ?")
            params.append(duration)
        if file_size_bytes is not None:
            updates.append("file_size_bytes = ?")
            params.append(file_size_bytes)
        if error_message:
            updates.append("error_message = ?")
            params.append(error_message)

        if not updates:
            return None

        params.append(job_id)
        sql = f"UPDATE tts_jobs SET {', '.join(updates)} WHERE job_id = ?"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, tuple(params))
            conn.commit()

            cursor.execute("SELECT * FROM tts_jobs WHERE job_id = ?", (job_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def count_active_jobs_for_device(self, device_id: str) -> int:
        """Counts pending and processing jobs for a device."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM tts_jobs WHERE device_id = ? AND status IN ('queued', 'processing')",
                (device_id.strip(),),
            )
            row = cursor.fetchone()
            return row[0] if row else 0

    # ========================================================================
    # Billing & Subscription Management Helpers
    # ========================================================================

    def get_device_raw(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Internal helper: Returns raw SQLite row dictionary for a device."""
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
        """Toggles whether a subscription auto-renews at the end of the 30-day period."""
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
        """Cancels future subscription renewals while preserving Pro features until period end."""
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
        """Syncs subscription cancellation by Stripe Subscription ID from webhooks."""
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


# Global singleton database instance
billing_db = BillingDB()
