import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

DB_PATH = Path(__file__).resolve().parents[2] / "bot_stats.sqlite3"
TZ = ZoneInfo("Europe/Moscow")


def now_iso() -> str:
    return datetime.now(TZ).isoformat(timespec="seconds")


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_stats_db() -> None:
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                first_seen TEXT NOT NULL,
                last_seen TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                event_type TEXT NOT NULL,
                value TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_events_created_at ON events(created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)")


def track_user(user) -> None:
    if not user:
        return

    timestamp = now_iso()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO users (user_id, username, first_name, last_name, first_seen, last_seen)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name,
                last_name = excluded.last_name,
                last_seen = excluded.last_seen
            """,
            (
                user.id,
                user.username,
                user.first_name,
                user.last_name,
                timestamp,
                timestamp,
            ),
        )


def log_event(user_id: int | None, event_type: str, value: str | None = None) -> None:
    with connect() as conn:
        conn.execute(
            "INSERT INTO events (user_id, event_type, value, created_at) VALUES (?, ?, ?, ?)",
            (user_id, event_type, value, now_iso()),
        )


def count_events(conn: sqlite3.Connection, event_type: str, since: datetime | None = None) -> int:
    if since is None:
        row = conn.execute(
            "SELECT COUNT(*) AS count FROM events WHERE event_type = ?",
            (event_type,),
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT COUNT(*) AS count FROM events WHERE event_type = ? AND created_at >= ?",
            (event_type, since.isoformat(timespec="seconds")),
        ).fetchone()
    return int(row["count"])


def get_stats_report() -> str:
    now = datetime.now(TZ)
    day_ago = now - timedelta(days=1)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    with connect() as conn:
        total_users = conn.execute("SELECT COUNT(*) AS count FROM users").fetchone()["count"]
        active_day = conn.execute(
            "SELECT COUNT(*) AS count FROM users WHERE last_seen >= ?",
            (day_ago.isoformat(timespec="seconds"),),
        ).fetchone()["count"]

        searches_day = count_events(conn, "search", day_ago)
        searches_week = count_events(conn, "search", week_ago)
        searches_month = count_events(conn, "search", month_ago)
        movie_opens_day = count_events(conn, "movie_open", day_ago)
        popular_day = count_events(conn, "popular", day_ago)

        top_rows = conn.execute(
            """
            SELECT value, COUNT(*) AS count
            FROM events
            WHERE event_type = 'search' AND created_at >= ? AND value IS NOT NULL
            GROUP BY value
            ORDER BY count DESC
            LIMIT 5
            """,
            (week_ago.isoformat(timespec="seconds"),),
        ).fetchall()

    top_searches = "\n".join(
        f"• {row['value']} — {row['count']}" for row in top_rows
    ) or "• пока нет данных"

    return (
        "📊 *Статистика KINOLINK*\n\n"
        f"👥 Пользователей всего: *{total_users}*\n"
        f"🟢 Активных за 24 часа: *{active_day}*\n\n"
        "🔍 *Поиски*\n"
        f"• за день: *{searches_day}*\n"
        f"• за неделю: *{searches_week}*\n"
        f"• за месяц: *{searches_month}*\n\n"
        "🎞 *Действия за день*\n"
        f"• открытий карточек: *{movie_opens_day}*\n"
        f"• открытий популярного: *{popular_day}*\n\n"
        "🏆 *Топ поисков за неделю*\n"
        f"{top_searches}"
    )
