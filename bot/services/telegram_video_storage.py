import logging
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.types import MessageEntity

DB_PATH = Path(__file__).resolve().parents[2] / "telegram_videos.sqlite3"
TZ = ZoneInfo("Europe/Moscow")
logger = logging.getLogger(__name__)


@dataclass
class ParsedVideoCaption:
    content_type: str
    title: str
    year: int | None
    season: int | None
    episode: int | None
    voiceover: str
    imdb_id: str


def now_iso() -> str:
    return datetime.now(TZ).isoformat(timespec="seconds")


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_telegram_video_db() -> None:
    with connect() as conn:
        columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(telegram_videos)").fetchall()
        }

        if columns and "content_type" not in columns:
            _rebuild_telegram_video_table(conn, columns)

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS telegram_videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_type TEXT NOT NULL,
                title TEXT NOT NULL,
                year INTEGER,
                season INTEGER,
                episode INTEGER,
                voiceover TEXT NOT NULL,
                imdb_id TEXT NOT NULL,
                media_type TEXT NOT NULL,
                file_id TEXT NOT NULL,
                file_unique_id TEXT NOT NULL,
                storage_chat_id INTEGER NOT NULL,
                message_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_telegram_videos_imdb_id ON telegram_videos(imdb_id)"
        )
        conn.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_telegram_videos_unique_release
            ON telegram_videos (
                imdb_id,
                content_type,
                COALESCE(season, 0),
                COALESCE(episode, 0),
                voiceover
            )
            """
        )


def _rebuild_telegram_video_table(conn: sqlite3.Connection, columns: set[str]) -> None:
    logger.info("Migrating telegram_videos table to content_type/voiceover schema")
    conn.execute(
        """
        CREATE TABLE telegram_videos_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_type TEXT NOT NULL,
            title TEXT NOT NULL,
            year INTEGER,
            season INTEGER,
            episode INTEGER,
            voiceover TEXT NOT NULL,
            imdb_id TEXT NOT NULL,
            media_type TEXT NOT NULL,
            file_id TEXT NOT NULL,
            file_unique_id TEXT NOT NULL,
            storage_chat_id INTEGER NOT NULL,
            message_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        INSERT INTO telegram_videos_new (
            id, content_type, title, year, season, episode, voiceover, imdb_id,
            media_type, file_id, file_unique_id, storage_chat_id, message_id,
            created_at, updated_at
        )
        SELECT
            id,
            'movie',
            title,
            year,
            NULL,
            NULL,
            COALESCE(NULLIF(voiceover, ''), 'Не указана'),
            imdb_id,
            media_type,
            file_id,
            file_unique_id,
            storage_chat_id,
            message_id,
            created_at,
            updated_at
        FROM telegram_videos
        """
    )
    conn.execute("DROP TABLE telegram_videos")
    conn.execute("ALTER TABLE telegram_videos_new RENAME TO telegram_videos")


def normalize_content_type(value: str | None) -> str | None:
    if not value:
        return None

    normalized = value.strip().casefold()
    if normalized in {"фильм", "movie", "film", "кино"}:
        return "movie"
    if normalized in {"сериал", "series", "serial", "tv", "show"}:
        return "series"
    return None


def normalize_imdb_id(value: str) -> str:
    return value.strip().lower()


def parse_video_caption(caption: str | None) -> ParsedVideoCaption | None:
    if not caption:
        return None

    lines = [line.strip() for line in caption.splitlines() if line.strip()]
    if not lines:
        return None

    title = None
    year = None
    season = None
    episode = None
    voiceover = None
    imdb_id = None
    content_type = None

    for line in lines:
        key_value = re.match(r"^\s*([^:：]+)\s*[:：]\s*(.+?)\s*$", line)
        if not key_value:
            continue

        key = key_value.group(1).strip().casefold()
        value = key_value.group(2).strip()

        if key in {"тип", "type", "content_type"}:
            content_type = normalize_content_type(value)
        elif key in {"название", "title", "name"}:
            title = value
        elif key in {"год", "year"}:
            year_match = re.search(r"\b(19|20)\d{2}\b", value)
            if year_match:
                year = int(year_match.group(0))
        elif key in {"сезон", "season"}:
            season_match = re.search(r"\d+", value)
            if season_match:
                season = int(season_match.group(0))
        elif key in {"серия", "episode", "эпизод"}:
            episode_match = re.search(r"\d+", value)
            if episode_match:
                episode = int(episode_match.group(0))
        elif key in {"озвучка", "voiceover", "voice"}:
            voiceover = value
        elif key in {"imdb", "imdb id", "imdb_id"}:
            imdb_match = re.search(r"\btt\d{5,12}\b", value, flags=re.IGNORECASE)
            if imdb_match:
                imdb_id = normalize_imdb_id(imdb_match.group(0))

    if not imdb_id:
        imdb_match = re.search(r"\btt\d{5,12}\b", caption, flags=re.IGNORECASE)
        if imdb_match:
            imdb_id = normalize_imdb_id(imdb_match.group(0))

    if not voiceover:
        voice_match = re.search(r"озвучка\s*[:：]\s*(.+)", caption, flags=re.IGNORECASE)
        if voice_match:
            voiceover = voice_match.group(1).strip()

    if season is None:
        season_match = re.search(r"(?:сезон|season)\s*[:：]?\s*(\d+)", caption, flags=re.IGNORECASE)
        if season_match:
            season = int(season_match.group(1))

    if episode is None:
        episode_match = re.search(r"(?:серия|episode|эпизод)\s*[:：]?\s*(\d+)", caption, flags=re.IGNORECASE)
        if episode_match:
            episode = int(episode_match.group(1))

    if not title:
        title_line = next(
            (
                line
                for line in lines
                if not re.match(r"^\s*(озвучка|voiceover|voice|imdb|год|year)\s*[:：]", line, re.IGNORECASE)
            ),
            None,
        )
        if title_line:
            title = re.sub(r"\btt\d{5,12}\b", "", title_line, flags=re.IGNORECASE).strip()

    if title and year is None:
        year_match = re.search(r"(?:\(|\b)((?:19|20)\d{2})(?:\)|\b)", title)
        if year_match:
            year = int(year_match.group(1))
            title = re.sub(r"\s*\(?\b(?:19|20)\d{2}\b\)?\s*", " ", title).strip()

    if content_type is None:
        content_type = "series" if season is not None or episode is not None else "movie"

    if content_type == "movie":
        season = None
        episode = None

    if content_type == "series" and (season is None or episode is None):
        return None

    if not title or not imdb_id or not voiceover:
        return None

    return ParsedVideoCaption(
        content_type=content_type,
        title=title,
        year=year,
        season=season,
        episode=episode,
        voiceover=voiceover,
        imdb_id=imdb_id,
    )


def save_telegram_video(
    *,
    title: str,
    year: int | None,
    season: int | None,
    episode: int | None,
    voiceover: str,
    imdb_id: str,
    content_type: str,
    media_type: str,
    file_id: str,
    file_unique_id: str,
    storage_chat_id: int,
    message_id: int,
) -> None:
    timestamp = now_iso()
    normalized_imdb_id = normalize_imdb_id(imdb_id)
    season_key = season or 0
    episode_key = episode or 0

    with connect() as conn:
        cursor = conn.execute(
            """
            UPDATE telegram_videos SET
                title = ?,
                year = ?,
                season = ?,
                episode = ?,
                voiceover = ?,
                media_type = ?,
                file_id = ?,
                file_unique_id = ?,
                storage_chat_id = ?,
                message_id = ?,
                updated_at = ?
            WHERE
                imdb_id = ?
                AND content_type = ?
                AND COALESCE(season, 0) = ?
                AND COALESCE(episode, 0) = ?
                AND voiceover = ?
            """,
            (
                title,
                year,
                season,
                episode,
                voiceover,
                media_type,
                file_id,
                file_unique_id,
                storage_chat_id,
                message_id,
                timestamp,
                normalized_imdb_id,
                content_type,
                season_key,
                episode_key,
                voiceover,
            ),
        )

        if cursor.rowcount:
            return

        conn.execute(
            """
            INSERT INTO telegram_videos (
                content_type, title, year, season, episode, voiceover, imdb_id, media_type,
                file_id, file_unique_id, storage_chat_id, message_id, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                content_type,
                title,
                year,
                season,
                episode,
                voiceover,
                normalized_imdb_id,
                media_type,
                file_id,
                file_unique_id,
                storage_chat_id,
                message_id,
                timestamp,
                timestamp,
            ),
        )


def get_telegram_videos(imdb_id: str, content_type: str | None = None) -> list[sqlite3.Row]:
    with connect() as conn:
        if content_type:
            rows = conn.execute(
                """
                SELECT * FROM telegram_videos
                WHERE imdb_id = ? AND content_type = ?
                ORDER BY season, episode, voiceover
                """,
                (normalize_imdb_id(imdb_id), content_type),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT * FROM telegram_videos
                WHERE imdb_id = ?
                ORDER BY content_type, season, episode, voiceover
                """,
                (normalize_imdb_id(imdb_id),),
            ).fetchall()
    return list(rows)


def get_available_seasons(imdb_id: str) -> list[int]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT DISTINCT season FROM telegram_videos
            WHERE imdb_id = ? AND content_type = 'series' AND season IS NOT NULL
            ORDER BY season
            """,
            (normalize_imdb_id(imdb_id),),
        ).fetchall()
    return [int(row["season"]) for row in rows]


def get_available_episodes(imdb_id: str, season: int) -> list[int]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT DISTINCT episode FROM telegram_videos
            WHERE imdb_id = ? AND content_type = 'series' AND season = ? AND episode IS NOT NULL
            ORDER BY episode
            """,
            (normalize_imdb_id(imdb_id), season),
        ).fetchall()
    return [int(row["episode"]) for row in rows]


def get_movie_voiceovers(imdb_id: str) -> list[sqlite3.Row]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM telegram_videos
            WHERE imdb_id = ? AND content_type = 'movie'
            ORDER BY voiceover
            """,
            (normalize_imdb_id(imdb_id),),
        ).fetchall()
    return list(rows)


def get_episode_voiceovers(imdb_id: str, season: int, episode: int) -> list[sqlite3.Row]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM telegram_videos
            WHERE imdb_id = ? AND content_type = 'series' AND season = ? AND episode = ?
            ORDER BY voiceover
            """,
            (normalize_imdb_id(imdb_id), season, episode),
        ).fetchall()
    return list(rows)


def get_telegram_video_by_id(record_id: int) -> sqlite3.Row | None:
    with connect() as conn:
        return conn.execute(
            "SELECT * FROM telegram_videos WHERE id = ?",
            (record_id,),
        ).fetchone()


def get_next_episode_record(video: sqlite3.Row) -> sqlite3.Row | None:
    if video["content_type"] != "series":
        return None

    with connect() as conn:
        return conn.execute(
            """
            SELECT * FROM telegram_videos
            WHERE
                imdb_id = ?
                AND content_type = 'series'
                AND voiceover = ?
                AND (
                    season > ?
                    OR (season = ? AND episode > ?)
                )
            ORDER BY season, episode
            LIMIT 1
            """,
            (
                video["imdb_id"],
                video["voiceover"],
                video["season"],
                video["season"],
                video["episode"],
            ),
        ).fetchone()


def format_record_title(video: sqlite3.Row) -> str:
    if video["content_type"] == "series":
        return (
            f"{video['title']} "
            f"{video['season']} сезон {video['episode']} серия"
            f" — {video['voiceover']}"
        )
    return f"{video['title']} — {video['voiceover']}"


def telegram_offset(text: str) -> int:
    return len(text.encode("utf-16-le")) // 2


def build_delivery_caption(
    video: sqlite3.Row,
    bot_username: str | None,
) -> tuple[str, list[MessageEntity]]:
    icon = "📺" if video["content_type"] == "series" else "🎬"
    lines = [f"{icon} {video['title']}"]

    if video["year"]:
        lines.append(f"📅 Год: {video['year']}")

    if video["content_type"] == "series":
        lines.append(f"📌 Сезон: {video['season']}")
        lines.append(f"🎞 Серия: {video['episode']}")

    lines.append(f"🎧 Озвучка: {video['voiceover']}")

    body = "\n".join(lines)
    footer_icon = "🎬"
    footer = f"{footer_icon} KINOLINK"
    caption = f"{body}\n\n{footer}"
    footer_offset = telegram_offset(f"{body}\n\n")
    entities = []

    if bot_username:
        entities.append(
            MessageEntity(
                type="text_link",
                offset=footer_offset + telegram_offset(f"{footer_icon} "),
                length=telegram_offset("KINOLINK"),
                url=f"https://t.me/{bot_username}",
            )
        )

    return caption, entities


async def send_video_record_to_user(bot: Bot, user_chat_id: int, record_id: int) -> bool:
    video = get_telegram_video_by_id(record_id)
    if not video:
        return False

    bot_info = await bot.get_me()
    caption, caption_entities = build_delivery_caption(video, bot_info.username)

    try:
        if video["media_type"] == "video":
            await bot.send_video(
                chat_id=user_chat_id,
                video=video["file_id"],
                caption=caption,
                caption_entities=caption_entities,
            )
        elif video["media_type"] == "document":
            await bot.send_document(
                chat_id=user_chat_id,
                document=video["file_id"],
                caption=caption,
                caption_entities=caption_entities,
            )
        else:
            logger.warning("Unsupported Telegram media_type: %s", video["media_type"])
            return False
        return True
    except TelegramAPIError as exc:
        logger.warning(
            "Failed to send Telegram video by file_id for record_id=%s, trying copy_message: %s",
            record_id,
            exc,
        )

    try:
        await bot.copy_message(
            chat_id=user_chat_id,
            from_chat_id=video["storage_chat_id"],
            message_id=video["message_id"],
            caption=caption,
            caption_entities=caption_entities,
        )
        return True
    except TelegramAPIError as exc:
        logger.warning("Failed to copy Telegram video for record_id=%s: %s", record_id, exc)
        return False
