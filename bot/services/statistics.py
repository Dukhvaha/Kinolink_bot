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
        conn.execute("CREATE INDEX IF NOT EXISTS idx_users_last_seen ON users(last_seen)")


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


def touch_user(user_id: int | None, username: str | None = None, first_name: str | None = None) -> None:
    if not user_id:
        return

    timestamp = now_iso()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO users (user_id, username, first_name, last_name, first_seen, last_seen)
            VALUES (?, ?, ?, NULL, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = COALESCE(excluded.username, users.username),
                first_name = COALESCE(excluded.first_name, users.first_name),
                last_seen = excluded.last_seen
            """,
            (user_id, username, first_name, timestamp, timestamp),
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


def count_active_users(conn: sqlite3.Connection, since: datetime) -> int:
    row = conn.execute(
        "SELECT COUNT(*) AS count FROM users WHERE last_seen >= ?",
        (since.isoformat(timespec="seconds"),),
    ).fetchone()
    return int(row["count"])


def count_events_by_types(
    conn: sqlite3.Connection,
    event_types: tuple[str, ...],
    since: datetime | None = None,
) -> int:
    placeholders = ",".join("?" for _ in event_types)
    params: list[str] = list(event_types)
    where = f"event_type IN ({placeholders})"

    if since is not None:
        where += " AND created_at >= ?"
        params.append(since.isoformat(timespec="seconds"))

    row = conn.execute(
        f"SELECT COUNT(*) AS count FROM events WHERE {where}",
        params,
    ).fetchone()
    return int(row["count"])


def top_search(conn: sqlite3.Connection, event_type: str, since: datetime) -> str:
    row = conn.execute(
        """
        SELECT value, COUNT(*) AS count
        FROM events
        WHERE event_type = ? AND created_at >= ? AND value IS NOT NULL AND value != ''
        GROUP BY value
        ORDER BY count DESC, value ASC
        LIMIT 1
        """,
        (event_type, since.isoformat(timespec="seconds")),
    ).fetchone()

    if not row:
        return "пока нет данных"

    return f"{row['value']} — {row['count']}"


def get_stats_report() -> str:
    now = datetime.now(TZ)
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    with connect() as conn:
        total_users = conn.execute("SELECT COUNT(*) AS count FROM users").fetchone()["count"]
        active_day = count_active_users(conn, day_start)
        active_week = count_active_users(conn, week_ago)
        active_month = count_active_users(conn, month_ago)

        searches_day = count_events(conn, "search", day_start)
        searches_week = count_events(conn, "search", week_ago)
        searches_month = count_events(conn, "search", month_ago)
        movie_opens_day = count_events(conn, "movie_open", day_start)
        mini_app_day = count_events(conn, "mini_app_open", day_start)
        site_open_day = count_events(conn, "site_open", day_start)
        telegram_video_day = count_events(conn, "telegram_video_sent", day_start)
        openings_day = count_events_by_types(
            conn,
            ("movie_open", "mini_app_open", "site_open", "telegram_video_sent"),
            day_start,
        )
        top_movie = top_search(conn, "search_movie", month_ago)
        top_series = top_search(conn, "search_series", month_ago)

    return (
        "📊 *Статистика KINOLINK*\n\n"
        f"👥 Всего пользователей: *{total_users}*\n"
        f"🟢 Активные сегодня: *{active_day}*\n"
        f"📅 Активные за неделю: *{active_week}*\n"
        f"📆 Активные за месяц: *{active_month}*\n\n"
        "🔍 *Поиски*\n"
        f"• сегодня: *{searches_day}*\n"
        f"• за неделю: *{searches_week}*\n"
        f"• за месяц: *{searches_month}*\n\n"
        "🎞 *Открытия сегодня*\n"
        f"• карточек фильмов/сериалов: *{movie_opens_day}*\n"
        f"• Mini App: *{mini_app_day}*\n"
        f"• сайта: *{site_open_day}*\n"
        f"• Telegram-видео: *{telegram_video_day}*\n"
        f"• всего открытий: *{openings_day}*\n\n"
        "🏆 *Популярное за месяц*\n"
        f"• фильм: *{top_movie}*\n"
        f"• сериал: *{top_series}*"
    )
