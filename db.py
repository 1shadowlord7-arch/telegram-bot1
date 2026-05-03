
import json
import os
import re
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

from config import DB_FILE, MONGO_DB_NAME, MONGO_URI

DB_PATH = Path(DB_FILE)


@contextmanager
def conn():
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    finally:
        con.close()


def init_db():
    with conn() as con:
        cur = con.cursor()

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                photo_file_id TEXT DEFAULT '',
                started INTEGER DEFAULT 0,
                created_at INTEGER DEFAULT (strftime('%s','now'))
            )
            """
        )
        cur.execute("PRAGMA table_info(users)")
        user_cols = {r["name"] for r in cur.fetchall()}
        if "photo_file_id" not in user_cols:
            cur.execute("ALTER TABLE users ADD COLUMN photo_file_id TEXT DEFAULT ''")

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS groups (
                chat_id INTEGER PRIMARY KEY,
                title TEXT,
                connected_channel_id INTEGER,
                request_limit INTEGER DEFAULT 1,
                bad_words_json TEXT DEFAULT '[]',
                warn_limit INTEGER DEFAULT 3,
                spam_on INTEGER DEFAULT 0,
                spam_limit INTEGER DEFAULT 5,
                created_at INTEGER DEFAULT (strftime('%s','now'))
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER,
                user_id INTEGER,
                username TEXT,
                full_name TEXT,
                text TEXT,
                status TEXT DEFAULT 'pending',
                note TEXT DEFAULT '',
                created_at INTEGER DEFAULT (strftime('%s','now')),
                updated_at INTEGER DEFAULT (strftime('%s','now'))
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS warnings (
                group_id INTEGER,
                user_id INTEGER,
                warn_count INTEGER DEFAULT 0,
                last_reason TEXT DEFAULT '',
                updated_at INTEGER DEFAULT (strftime('%s','now')),
                PRIMARY KEY (group_id, user_id)
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS states (
                user_id INTEGER,
                chat_id INTEGER,
                action TEXT,
                data_json TEXT DEFAULT '{}',
                updated_at INTEGER DEFAULT (strftime('%s','now')),
                PRIMARY KEY (user_id, chat_id)
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS channel_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER,
                message_id INTEGER,
                searchable_text TEXT,
                created_at INTEGER DEFAULT (strftime('%s','now'))
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS challenge_links (
                id TEXT PRIMARY KEY,
                game_type TEXT,
                group_id INTEGER,
                challenger_id INTEGER,
                target_id INTEGER,
                status TEXT DEFAULT 'pending',
                meta_json TEXT DEFAULT '{}',
                created_at INTEGER DEFAULT (strftime('%s','now'))
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS friend_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_user_id INTEGER,
                to_user_id INTEGER,
                status TEXT DEFAULT 'pending',
                note TEXT DEFAULT '',
                created_at INTEGER DEFAULT (strftime('%s','now')),
                updated_at INTEGER DEFAULT (strftime('%s','now'))
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS friends (
                user_low INTEGER,
                user_high INTEGER,
                created_at INTEGER DEFAULT (strftime('%s','now')),
                PRIMARY KEY (user_low, user_high)
            )
            """
        )


def _fullname(user):
    return (user.first_name or "") + (" " + user.last_name if getattr(user, "last_name", None) else "")


def normalize_pair(a: int, b: int):
    return (a, b) if a < b else (b, a)


def upsert_user(user, photo_file_id: str = ""):
    with conn() as con:
        con.execute(
            """
            INSERT INTO users (user_id, username, full_name, photo_file_id, started)
            VALUES (?, ?, ?, ?, COALESCE((SELECT started FROM users WHERE user_id=?), 0))
            ON CONFLICT(user_id) DO UPDATE SET
                username=excluded.username,
                full_name=excluded.full_name,
                photo_file_id=COALESCE(NULLIF(excluded.photo_file_id, ''), users.photo_file_id)
            """,
            (user.id, user.username or "", _fullname(user), photo_file_id or "", user.id),
        )


def upsert_web_user(user_id: int, username: str = "", full_name: str = "", photo_file_id: str = ""):
    with conn() as con:
        con.execute(
            """
            INSERT INTO users (user_id, username, full_name, photo_file_id, started)
            VALUES (?, ?, ?, ?, COALESCE((SELECT started FROM users WHERE user_id=?), 0))
            ON CONFLICT(user_id) DO UPDATE SET
                username=excluded.username,
                full_name=excluded.full_name,
                photo_file_id=COALESCE(NULLIF(excluded.photo_file_id, ''), users.photo_file_id)
            """,
            (user_id, username or "", full_name or "", photo_file_id or "", user_id),
        )


def set_user_photo(user_id: int, photo_file_id: str):
    with conn() as con:
        con.execute("UPDATE users SET photo_file_id=? WHERE user_id=?", (photo_file_id, user_id))


def mark_started(user_id: int):
    with conn() as con:
        con.execute("UPDATE users SET started=1 WHERE user_id=?", (user_id,))


def get_user(user_id: int):
    with conn() as con:
        row = con.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
        return dict(row) if row else None


def user_by_username(username: str):
    username = username.lstrip("@").lower()
    with conn() as con:
        row = con.execute("SELECT * FROM users WHERE lower(username)=?", (username,)).fetchone()
        return dict(row) if row else None


def upsert_group(chat_id: int, title: str):
    with conn() as con:
        con.execute(
            """
            INSERT INTO groups (chat_id, title)
            VALUES (?, ?)
            ON CONFLICT(chat_id) DO UPDATE SET title=excluded.title
            """,
            (chat_id, title),
        )


def get_group(chat_id: int):
    with conn() as con:
        row = con.execute("SELECT * FROM groups WHERE chat_id=?", (chat_id,)).fetchone()
        return dict(row) if row else None


def list_groups():
    with conn() as con:
        rows = con.execute("SELECT * FROM groups ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]


def set_group_value(chat_id: int, key: str, value):
    if key not in {"connected_channel_id", "request_limit", "bad_words_json", "warn_limit", "spam_on", "spam_limit"}:
        raise ValueError(f"Unsupported group key: {key}")
    with conn() as con:
        con.execute(f"UPDATE groups SET {key}=? WHERE chat_id=?", (value, chat_id))


def get_bad_words(chat_id: int):
    g = get_group(chat_id)
    if not g:
        return []
    try:
        return json.loads(g.get("bad_words_json") or "[]")
    except Exception:
        return []


def add_bad_words(chat_id: int, words):
    existing = get_bad_words(chat_id)
    seen = {w.lower() for w in existing}
    for w in words:
        w = w.strip().lower()
        if w and w not in seen:
            existing.append(w)
            seen.add(w)
    set_group_value(chat_id, "bad_words_json", json.dumps(existing, ensure_ascii=False))


def set_state(user_id: int, chat_id: int, action: str, data: dict | None = None):
    with conn() as con:
        con.execute(
            """
            INSERT INTO states (user_id, chat_id, action, data_json)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, chat_id) DO UPDATE SET
                action=excluded.action,
                data_json=excluded.data_json,
                updated_at=(strftime('%s','now'))
            """,
            (user_id, chat_id, action, json.dumps(data or {}, ensure_ascii=False)),
        )


def get_state(user_id: int, chat_id: int):
    with conn() as con:
        row = con.execute("SELECT * FROM states WHERE user_id=? AND chat_id=?", (user_id, chat_id)).fetchone()
        if not row:
            return None
        data = dict(row)
        try:
            data["data"] = json.loads(data["data_json"] or "{}")
        except Exception:
            data["data"] = {}
        return data


def clear_state(user_id: int, chat_id: int):
    with conn() as con:
        con.execute("DELETE FROM states WHERE user_id=? AND chat_id=?", (user_id, chat_id))


def index_channel_post(channel_id: int, message_id: int, searchable_text: str):
    searchable_text = (searchable_text or "").strip()
    if not searchable_text:
        return
    with conn() as con:
        con.execute(
            "INSERT INTO channel_posts (channel_id, message_id, searchable_text) VALUES (?, ?, ?)",
            (channel_id, message_id, searchable_text[:5000]),
        )


def search_channel_posts(channel_id: int, query: str):
    q = f"%{query.lower()}%"
    with conn() as con:
        row = con.execute(
            """
            SELECT * FROM channel_posts
            WHERE channel_id=? AND lower(searchable_text) LIKE ?
            ORDER BY created_at ASC
            LIMIT 1
            """,
            (channel_id, q),
        ).fetchone()
        return dict(row) if row else None


def add_request(group_id: int, user, text: str):
    with conn() as con:
        cur = con.execute(
            """
            INSERT INTO requests (group_id, user_id, username, full_name, text)
            VALUES (?, ?, ?, ?, ?)
            """,
            (group_id, user.id, user.username or "", _fullname(user), text),
        )
        return cur.lastrowid


def count_open_requests(group_id: int, user_id: int):
    with conn() as con:
        row = con.execute(
            "SELECT COUNT(*) AS c FROM requests WHERE group_id=? AND user_id=? AND status IN ('pending','working')",
            (group_id, user_id),
        ).fetchone()
        return int(row["c"]) if row else 0


def requests_for_user(user_id: int):
    with conn() as con:
        rows = con.execute("SELECT * FROM requests WHERE user_id=? ORDER BY created_at ASC", (user_id,)).fetchall()
        return [dict(r) for r in rows]


def requests_for_group(group_id: int):
    with conn() as con:
        rows = con.execute(
            "SELECT * FROM requests WHERE group_id=? ORDER BY CASE status WHEN 'pending' THEN 0 WHEN 'working' THEN 1 WHEN 'done' THEN 2 ELSE 3 END, created_at ASC",
            (group_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def update_request_status(req_id: int, status: str, note: str = ""):
    with conn() as con:
        con.execute(
            "UPDATE requests SET status=?, note=?, updated_at=(strftime('%s','now')) WHERE id=?",
            (status, note, req_id),
        )


def get_request(req_id: int):
    with conn() as con:
        row = con.execute("SELECT * FROM requests WHERE id=?", (req_id,)).fetchone()
        return dict(row) if row else None


def inc_warning(group_id: int, user_id: int, reason: str = ""):
    with conn() as con:
        row = con.execute("SELECT warn_count FROM warnings WHERE group_id=? AND user_id=?", (group_id, user_id)).fetchone()
        count = int(row["warn_count"]) + 1 if row else 1
        con.execute(
            """
            INSERT INTO warnings (group_id, user_id, warn_count, last_reason)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(group_id, user_id) DO UPDATE SET
                warn_count=excluded.warn_count,
                last_reason=excluded.last_reason,
                updated_at=(strftime('%s','now'))
            """,
            (group_id, user_id, count, reason),
        )
        return count


def dec_warning(group_id: int, user_id: int):
    with conn() as con:
        row = con.execute("SELECT warn_count FROM warnings WHERE group_id=? AND user_id=?", (group_id, user_id)).fetchone()
        count = max(0, int(row["warn_count"]) - 1) if row else 0
        if count <= 0:
            con.execute("DELETE FROM warnings WHERE group_id=? AND user_id=?", (group_id, user_id))
        else:
            con.execute("UPDATE warnings SET warn_count=?, updated_at=(strftime('%s','now')) WHERE group_id=? AND user_id=?", (count, group_id, user_id))
        return count


def get_warning_count(group_id: int, user_id: int):
    with conn() as con:
        row = con.execute("SELECT warn_count FROM warnings WHERE group_id=? AND user_id=?", (group_id, user_id)).fetchone()
        return int(row["warn_count"]) if row else 0


def reset_warnings(group_id: int, user_id: int):
    with conn() as con:
        con.execute("DELETE FROM warnings WHERE group_id=? AND user_id=?", (group_id, user_id))


def add_challenge(ch_id: str, game_type: str, group_id: int, challenger_id: int, target_id: int, meta: dict | None = None):
    with conn() as con:
        con.execute(
            "INSERT OR REPLACE INTO challenge_links (id, game_type, group_id, challenger_id, target_id, status, meta_json) VALUES (?, ?, ?, ?, ?, 'pending', ?)",
            (ch_id, game_type, group_id, challenger_id, target_id, json.dumps(meta or {}, ensure_ascii=False)),
        )


def get_challenge(ch_id: str):
    with conn() as con:
        row = con.execute("SELECT * FROM challenge_links WHERE id=?", (ch_id,)).fetchone()
        if not row:
            return None
        data = dict(row)
        try:
            data["meta"] = json.loads(data.get("meta_json") or "{}")
        except Exception:
            data["meta"] = {}
        return data


def update_challenge(ch_id: str, status: str):
    with conn() as con:
        con.execute("UPDATE challenge_links SET status=? WHERE id=?", (status, ch_id))


# --- friends ---
def friend_count(user_id: int):
    with conn() as con:
        row = con.execute(
            "SELECT COUNT(*) AS c FROM friends WHERE user_low=? OR user_high=?",
            (user_id, user_id),
        ).fetchone()
        return int(row["c"]) if row else 0


def are_friends(a: int, b: int):
    low, high = normalize_pair(a, b)
    with conn() as con:
        row = con.execute(
            "SELECT 1 FROM friends WHERE user_low=? AND user_high=?",
            (low, high),
        ).fetchone()
        return bool(row)


def friend_request_exists(a: int, b: int):
    with conn() as con:
        row = con.execute(
            """
            SELECT * FROM friend_requests
            WHERE ((from_user_id=? AND to_user_id=?) OR (from_user_id=? AND to_user_id=?))
              AND status='pending'
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (a, b, b, a),
        ).fetchone()
        return dict(row) if row else None


def create_friend_request(from_user_id: int, to_user_id: int, note: str = ""):
    with conn() as con:
        cur = con.execute(
            """
            INSERT INTO friend_requests (from_user_id, to_user_id, status, note)
            VALUES (?, ?, 'pending', ?)
            """,
            (from_user_id, to_user_id, note),
        )
        return cur.lastrowid


def get_friend_request(req_id: int):
    with conn() as con:
        row = con.execute("SELECT * FROM friend_requests WHERE id=?", (req_id,)).fetchone()
        return dict(row) if row else None


def pending_friend_requests_for_user(user_id: int):
    with conn() as con:
        rows = con.execute(
            "SELECT * FROM friend_requests WHERE to_user_id=? AND status='pending' ORDER BY created_at ASC",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def update_friend_request(req_id: int, status: str, note: str = ""):
    with conn() as con:
        con.execute(
            "UPDATE friend_requests SET status=?, note=?, updated_at=(strftime('%s','now')) WHERE id=?",
            (status, note, req_id),
        )


def add_friend(a: int, b: int):
    low, high = normalize_pair(a, b)
    with conn() as con:
        con.execute(
            "INSERT OR IGNORE INTO friends (user_low, user_high) VALUES (?, ?)",
            (low, high),
        )


def remove_friend(a: int, b: int):
    low, high = normalize_pair(a, b)
    with conn() as con:
        con.execute(
            "DELETE FROM friends WHERE user_low=? AND user_high=?",
            (low, high),
        )


def friends_of(user_id: int):
    with conn() as con:
        rows = con.execute(
            "SELECT * FROM friends WHERE user_low=? OR user_high=? ORDER BY created_at DESC",
            (user_id, user_id),
        ).fetchall()
        friend_ids = []
        for r in rows:
            friend_ids.append(int(r["user_high"]) if int(r["user_low"]) == user_id else int(r["user_low"]))
        return friend_ids


# -------------------------
# MongoDB Atlas backend (optional)
# Set MONGO_URI to use Atlas. SQLite remains the fallback.
# -------------------------
USE_MONGO = bool(MONGO_URI)

if USE_MONGO:
    from pymongo import ASCENDING, DESCENDING, MongoClient, ReturnDocument

    _mongo_client = MongoClient(MONGO_URI)
    _mongo_db = _mongo_client[MONGO_DB_NAME]

    def _c(name: str):
        return _mongo_db[name]

    def _now():
        return int(time.time())

    def _doc(d):
        if not d:
            return None
        d = dict(d)
        d.pop("_id", None)
        return d

    def _next_seq(name: str) -> int:
        doc = _c("counters").find_one_and_update(
            {"_id": name},
            {"$inc": {"seq": 1}, "$setOnInsert": {"seq": 0}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return int(doc["seq"])

    def _pair(a: int, b: int):
        return (a, b) if a < b else (b, a)

    def init_db():
        _c("users").create_index("username")
        _c("groups").create_index([("created_at", DESCENDING)])
        _c("requests").create_index([("group_id", ASCENDING), ("status", ASCENDING), ("created_at", ASCENDING)])
        _c("requests").create_index([("user_id", ASCENDING), ("created_at", ASCENDING)])
        _c("warnings").create_index([("group_id", ASCENDING), ("user_id", ASCENDING)], unique=True)
        _c("states").create_index([("user_id", ASCENDING), ("chat_id", ASCENDING)], unique=True)
        _c("channel_posts").create_index([("channel_id", ASCENDING), ("created_at", ASCENDING)])
        _c("challenge_links").create_index("id", unique=True)
        _c("friend_requests").create_index([("to_user_id", ASCENDING), ("status", ASCENDING), ("created_at", ASCENDING)])
        _c("friends").create_index([("user_low", ASCENDING), ("user_high", ASCENDING)], unique=True)

    def upsert_user(user, photo_file_id: str = ""):
        _c("users").update_one(
            {"user_id": int(user.id)},
            {
                "$set": {
                    "username": user.username or "",
                    "full_name": _fullname(user),
                    **({"photo_file_id": photo_file_id} if photo_file_id else {}),
                },
                "$setOnInsert": {"started": 0, "created_at": _now()},
            },
            upsert=True,
        )

    def upsert_web_user(user_id: int, username: str = "", full_name: str = "", photo_file_id: str = ""):
        _c("users").update_one(
            {"user_id": int(user_id)},
            {
                "$set": {
                    "username": username or "",
                    "full_name": full_name or "",
                    **({"photo_file_id": photo_file_id} if photo_file_id else {}),
                },
                "$setOnInsert": {"started": 0, "created_at": _now()},
            },
            upsert=True,
        )

    def set_user_photo(user_id: int, photo_file_id: str):
        _c("users").update_one({"user_id": int(user_id)}, {"$set": {"photo_file_id": photo_file_id}})

    def mark_started(user_id: int):
        _c("users").update_one({"user_id": int(user_id)}, {"$set": {"started": 1}}, upsert=True)

    def get_user(user_id: int):
        return _doc(_c("users").find_one({"user_id": int(user_id)}))

    def user_by_username(username: str):
        username = username.lstrip("@").lower()
        return _doc(_c("users").find_one({"username": {"$regex": f"^{re.escape(username)}$", "$options": "i"}}))

    def upsert_group(chat_id: int, title: str):
        _c("groups").update_one(
            {"chat_id": int(chat_id)},
            {"$set": {"title": title}, "$setOnInsert": {"created_at": _now()}},
            upsert=True,
        )

    def get_group(chat_id: int):
        return _doc(_c("groups").find_one({"chat_id": int(chat_id)}))

    def list_groups():
        return [_doc(r) for r in _c("groups").find().sort("created_at", DESCENDING)]

    def set_group_value(chat_id: int, key: str, value):
        if key not in {"connected_channel_id", "request_limit", "bad_words_json", "warn_limit", "spam_on", "spam_limit"}:
            raise ValueError(f"Unsupported group key: {key}")
        _c("groups").update_one({"chat_id": int(chat_id)}, {"$set": {key: value}}, upsert=True)

    def get_bad_words(chat_id: int):
        g = get_group(chat_id) or {}
        try:
            return json.loads(g.get("bad_words_json") or "[]")
        except Exception:
            return []

    def add_bad_words(chat_id: int, words):
        existing = get_bad_words(chat_id)
        seen = {w.lower() for w in existing}
        for w in words:
            w = (w or "").strip().lower()
            if w and w not in seen:
                existing.append(w)
                seen.add(w)
        set_group_value(chat_id, "bad_words_json", json.dumps(existing, ensure_ascii=False))

    def set_state(user_id: int, chat_id: int, action: str, data: dict | None = None):
        _c("states").update_one(
            {"user_id": int(user_id), "chat_id": int(chat_id)},
            {"$set": {"action": action, "data_json": json.dumps(data or {}, ensure_ascii=False), "updated_at": _now()}},
            upsert=True,
        )

    def get_state(user_id: int, chat_id: int):
        row = _doc(_c("states").find_one({"user_id": int(user_id), "chat_id": int(chat_id)}))
        if not row:
            return None
        try:
            row["data"] = json.loads(row.get("data_json") or "{}")
        except Exception:
            row["data"] = {}
        return row

    def clear_state(user_id: int, chat_id: int):
        _c("states").delete_one({"user_id": int(user_id), "chat_id": int(chat_id)})

    def index_channel_post(channel_id: int, message_id: int, searchable_text: str):
        searchable_text = (searchable_text or "").strip()
        if not searchable_text:
            return
        _c("channel_posts").insert_one(
            {"channel_id": int(channel_id), "message_id": int(message_id), "searchable_text": searchable_text[:5000], "created_at": _now()}
        )

    def search_channel_posts(channel_id: int, query: str):
        q = (query or "").strip().lower()
        if not q:
            return None
        row = _c("channel_posts").find_one(
            {"channel_id": int(channel_id), "searchable_text": {"$regex": re.escape(q), "$options": "i"}},
            sort=[("created_at", ASCENDING)],
        )
        return _doc(row)

    def add_request(group_id: int, user, text: str):
        rid = _next_seq("requests")
        _c("requests").insert_one(
            {
                "id": rid,
                "group_id": int(group_id),
                "user_id": int(user.id),
                "username": user.username or "",
                "full_name": _fullname(user),
                "text": text,
                "status": "pending",
                "note": "",
                "created_at": _now(),
                "updated_at": _now(),
            }
        )
        return rid

    def count_open_requests(group_id: int, user_id: int):
        return _c("requests").count_documents({"group_id": int(group_id), "user_id": int(user_id), "status": {"$in": ["pending", "working"]}})

    def requests_for_user(user_id: int):
        rows = list(_c("requests").find({"user_id": int(user_id)}).sort("created_at", ASCENDING))
        return [_doc(r) for r in rows]

    def requests_for_group(group_id: int):
        rows = list(_c("requests").find({"group_id": int(group_id)}))
        rank = {"pending": 0, "working": 1, "done": 2, "cancelled": 3, "canceled": 3}
        rows.sort(key=lambda r: (rank.get(r.get("status"), 9), r.get("created_at", 0)))
        return [_doc(r) for r in rows]

    def update_request_status(req_id: int, status: str, note: str = ""):
        _c("requests").update_one({"id": int(req_id)}, {"$set": {"status": status, "note": note, "updated_at": _now()}})

    def get_request(req_id: int):
        return _doc(_c("requests").find_one({"id": int(req_id)}))

    def inc_warning(group_id: int, user_id: int, reason: str = ""):
        row = _doc(_c("warnings").find_one({"group_id": int(group_id), "user_id": int(user_id)})) or {}
        count = int(row.get("warn_count", 0)) + 1
        _c("warnings").update_one(
            {"group_id": int(group_id), "user_id": int(user_id)},
            {"$set": {"warn_count": count, "last_reason": reason, "updated_at": _now()}},
            upsert=True,
        )
        return count

    def dec_warning(group_id: int, user_id: int):
        row = _doc(_c("warnings").find_one({"group_id": int(group_id), "user_id": int(user_id)})) or {}
        count = max(0, int(row.get("warn_count", 0)) - 1)
        if count <= 0:
            _c("warnings").delete_one({"group_id": int(group_id), "user_id": int(user_id)})
        else:
            _c("warnings").update_one({"group_id": int(group_id), "user_id": int(user_id)}, {"$set": {"warn_count": count, "updated_at": _now()}})
        return count

    def get_warning_count(group_id: int, user_id: int):
        row = _doc(_c("warnings").find_one({"group_id": int(group_id), "user_id": int(user_id)})) or {}
        return int(row.get("warn_count", 0))

    def reset_warnings(group_id: int, user_id: int):
        _c("warnings").delete_one({"group_id": int(group_id), "user_id": int(user_id)})

    def add_challenge(ch_id: str, game_type: str, group_id: int, challenger_id: int, target_id: int, meta: dict | None = None):
        _c("challenge_links").update_one(
            {"id": ch_id},
            {
                "$set": {
                    "id": ch_id,
                    "game_type": game_type,
                    "group_id": int(group_id),
                    "challenger_id": int(challenger_id),
                    "target_id": int(target_id),
                    "status": "pending",
                    "meta_json": json.dumps(meta or {}, ensure_ascii=False),
                    "created_at": _now(),
                }
            },
            upsert=True,
        )

    def get_challenge(ch_id: str):
        row = _doc(_c("challenge_links").find_one({"id": ch_id}))
        if not row:
            return None
        try:
            row["meta"] = json.loads(row.get("meta_json") or "{}")
        except Exception:
            row["meta"] = {}
        return row

    def update_challenge(ch_id: str, status: str):
        _c("challenge_links").update_one({"id": ch_id}, {"$set": {"status": status}})

    def friend_count(user_id: int):
        return _c("friends").count_documents({"$or": [{"user_low": int(user_id)}, {"user_high": int(user_id)}]})

    def are_friends(a: int, b: int):
        low, high = _pair(a, b)
        return _c("friends").find_one({"user_low": low, "user_high": high}) is not None

    def friend_request_exists(a: int, b: int):
        row = _c("friend_requests").find_one(
            {"status": "pending", "$or": [{"from_user_id": int(a), "to_user_id": int(b)}, {"from_user_id": int(b), "to_user_id": int(a)}]},
            sort=[("created_at", DESCENDING)],
        )
        return _doc(row)

    def create_friend_request(from_user_id: int, to_user_id: int, note: str = ""):
        rid = _next_seq("friend_requests")
        _c("friend_requests").insert_one(
            {
                "id": rid,
                "from_user_id": int(from_user_id),
                "to_user_id": int(to_user_id),
                "status": "pending",
                "note": note,
                "created_at": _now(),
                "updated_at": _now(),
            }
        )
        return rid

    def get_friend_request(req_id: int):
        return _doc(_c("friend_requests").find_one({"id": int(req_id)}))

    def pending_friend_requests_for_user(user_id: int):
        rows = list(_c("friend_requests").find({"to_user_id": int(user_id), "status": "pending"}).sort("created_at", ASCENDING))
        return [_doc(r) for r in rows]

    def update_friend_request(req_id: int, status: str, note: str = ""):
        _c("friend_requests").update_one({"id": int(req_id)}, {"$set": {"status": status, "note": note, "updated_at": _now()}})

    def add_friend(a: int, b: int):
        low, high = _pair(a, b)
        _c("friends").update_one(
            {"user_low": low, "user_high": high},
            {"$setOnInsert": {"user_low": low, "user_high": high, "created_at": _now()}},
            upsert=True,
        )

    def remove_friend(a: int, b: int):
        low, high = _pair(a, b)
        _c("friends").delete_one({"user_low": low, "user_high": high})

    def friends_of(user_id: int):
        rows = list(_c("friends").find({"$or": [{"user_low": int(user_id)}, {"user_high": int(user_id)}]}).sort("created_at", DESCENDING))
        friend_ids = []
        for r in rows:
            friend_ids.append(int(r["user_high"]) if int(r["user_low"]) == int(user_id) else int(r["user_low"]))
        return friend_ids
