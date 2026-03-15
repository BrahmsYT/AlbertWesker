import sqlite3
from contextlib import contextmanager
from datetime import datetime
import hashlib

DB_PATH = "scanner.db"


def init_db():
    """Create tables if they don't exist."""
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS blacklist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT UNIQUE NOT NULL,
                reason TEXT NOT NULL DEFAULT '',
                added_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS whitelist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT UNIQUE NOT NULL,
                note TEXT NOT NULL DEFAULT '',
                added_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scan_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                domain TEXT NOT NULL,
                risk_score INTEGER NOT NULL,
                risk_label TEXT NOT NULL,
                finding_count INTEGER NOT NULL DEFAULT 0,
                category TEXT NOT NULL DEFAULT 'uncategorized',
                scanned_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Create default admin user if not exists
        admin = conn.execute("SELECT * FROM users WHERE username = 'admin'").fetchone()
        if not admin:
            password_hash = hash_password("admin123")
            conn.execute(
                "INSERT INTO users (username, email, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?)",
                ("admin", "admin@localhost", password_hash, "admin", datetime.utcnow().isoformat())
            )
            conn.commit()


@contextmanager
def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


# ── Blacklist ──

def add_to_blacklist(domain: str, reason: str = "") -> bool:
    """Add domain to blacklist. Returns False if already exists."""
    try:
        with _get_conn() as conn:
            conn.execute(
                "INSERT INTO blacklist (domain, reason, added_at) VALUES (?, ?, ?)",
                (domain.strip().lower(), reason.strip(), datetime.utcnow().isoformat()),
            )
        return True
    except sqlite3.IntegrityError:
        return False


def remove_from_blacklist(domain: str) -> bool:
    with _get_conn() as conn:
        cur = conn.execute("DELETE FROM blacklist WHERE domain = ?", (domain.strip().lower(),))
        return cur.rowcount > 0


def is_blacklisted(domain: str) -> bool:
    with _get_conn() as conn:
        row = conn.execute("SELECT 1 FROM blacklist WHERE domain = ?", (domain.strip().lower(),)).fetchone()
        return row is not None


def get_blacklist() -> list[dict]:
    with _get_conn() as conn:
        rows = conn.execute("SELECT id, domain, reason, added_at FROM blacklist ORDER BY added_at DESC").fetchall()
        return [dict(r) for r in rows]


# ── Whitelist ──

def add_to_whitelist(domain: str, note: str = "") -> bool:
    """Add domain to whitelist. Returns False if already exists."""
    try:
        with _get_conn() as conn:
            conn.execute(
                "INSERT INTO whitelist (domain, note, added_at) VALUES (?, ?, ?)",
                (domain.strip().lower(), note.strip(), datetime.utcnow().isoformat()),
            )
        return True
    except sqlite3.IntegrityError:
        return False


def remove_from_whitelist(domain: str) -> bool:
    with _get_conn() as conn:
        cur = conn.execute("DELETE FROM whitelist WHERE domain = ?", (domain.strip().lower(),))
        return cur.rowcount > 0


def is_whitelisted(domain: str) -> bool:
    with _get_conn() as conn:
        row = conn.execute("SELECT 1 FROM whitelist WHERE domain = ?", (domain.strip().lower(),)).fetchone()
        return row is not None


def get_whitelist() -> list[dict]:
    with _get_conn() as conn:
        rows = conn.execute("SELECT id, domain, note, added_at FROM whitelist ORDER BY added_at DESC").fetchall()
        return [dict(r) for r in rows]


# ── Scan History ──

def _categorize(risk_label: str) -> str:
    """Map risk label to a list category."""
    label = risk_label.lower()
    if label == "low":
        return "safe"        # auto-whitelist candidate
    if label == "medium":
        return "warning"     # needs attention
    if label in ("high", "critical"):
        return "dangerous"   # high risk - flagged for review
    return "uncategorized"


def save_scan(domain: str, risk_score: int, risk_label: str, finding_count: int, user_id: int = None) -> dict:
    """Save a scan result and auto-categorize it. Returns the saved row."""
    category = _categorize(risk_label)
    now = datetime.utcnow().isoformat()
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO scan_history (user_id, domain, risk_score, risk_label, finding_count, category, scanned_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, domain.strip().lower(), risk_score, risk_label, finding_count, category, now),
        )
    # Auto-add to whitelist if safe
    if category == "safe":
        add_to_whitelist(domain, note=f"Auto: {risk_label} risk (score {risk_score})")
    return {
        "domain": domain.strip().lower(),
        "risk_score": risk_score,
        "risk_label": risk_label,
        "finding_count": finding_count,
        "category": category,
        "scanned_at": now,
    }


def get_scan_history(category: str | None = None, user_id: int = None) -> list[dict]:
    """Get scan history, optionally filtered by category and/or user_id."""
    with _get_conn() as conn:
        query = "SELECT * FROM scan_history WHERE 1=1"
        params = []
        
        if category:
            query += " AND category = ?"
            params.append(category)
        
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        
        query += " ORDER BY scanned_at DESC"
        
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def get_scan_stats() -> dict:
    """Return counts per category."""
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT category, COUNT(*) as cnt FROM scan_history GROUP BY category"
        ).fetchall()
        stats = {r["category"]: r["cnt"] for r in rows}
        stats["total"] = sum(stats.values())
        return stats


def delete_scan(scan_id: int) -> bool:
    """Delete a scan from history by ID. Returns True if deleted."""
    with _get_conn() as conn:
        cur = conn.execute("DELETE FROM scan_history WHERE id = ?", (scan_id,))
        return cur.rowcount > 0


# ────────────────────────────────────────────
# USER AUTHENTICATION
# ────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()


def create_user(username: str, password: str, email: str = None, role: str = "user") -> dict:
    """Create a new user. Return user dict or None if username exists."""
    with _get_conn() as conn:
        try:
            password_hash = hash_password(password)
            conn.execute(
                "INSERT INTO users (username, email, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?)",
                (username, email, password_hash, role, datetime.utcnow().isoformat())
            )
            conn.commit()
            return get_user_by_username(username)
        except sqlite3.IntegrityError:
            return None


def get_user_by_username(username: str) -> dict:
    """Get user by username"""
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()
        return dict(row) if row else None


def verify_user(username: str, password: str) -> dict:
    """Verify username and password. Return user dict if valid, None otherwise."""
    user = get_user_by_username(username)
    if not user:
        return None
    
    password_hash = hash_password(password)
    if user["password_hash"] == password_hash:
        return user
    return None


def get_user_by_id(user_id: int) -> dict:
    """Get user by ID"""
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()
        return dict(row) if row else None
