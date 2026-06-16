import logging

from aiogram import Router
from aiogram.types import Message

from config import STORAGE_CHANNEL_ID
from bot.services.telegram_video_storage import (
    parse_video_caption,
    save_telegram_video,
)

router = Router()
logger = logging.getLogger(__name__)


def get_storage_channel_id() -> int | None:
    if not STORAGE_CHANNEL_ID:
        logger.warning("STORAGE_CHANNEL_ID is not set; storage channel posts will be ignored")
        return None

    try:
        return int(str(STORAGE_CHANNEL_ID).strip())
    except ValueError:
        logger.warning("Invalid STORAGE_CHANNEL_ID: %s", STORAGE_CHANNEL_ID)
        return None


def extract_media(message: Message) -> tuple[str, str, str] | None:
    if message.video:
        return "video", message.video.file_id, message.video.file_unique_id

    if message.document:
        return "document", message.document.file_id, message.document.file_unique_id

    return None


@router.channel_post()
async def index_storage_channel_post(message: Message):
    logger.info(
        "Channel post received: chat_id=%s message_id=%s has_video=%s has_document=%s caption=%s",
        message.chat.id,
        message.message_id,
        bool(message.video),
        bool(message.document),
        bool(message.caption),
    )

    storage_channel_id = get_storage_channel_id()
    if storage_channel_id is None:
        return

    if message.chat.id != storage_channel_id:
        logger.info(
            "Channel post ignored: chat_id=%s does not match STORAGE_CHANNEL_ID=%s",
            message.chat.id,
            storage_channel_id,
        )
        return

    media = extract_media(message)
    if not media:
        logger.info(
            "Storage channel post ignored: no video/document. chat_id=%s message_id=%s",
            message.chat.id,
            message.message_id,
        )
        return

    parsed_caption = parse_video_caption(message.caption)
    if not parsed_caption:
        logger.warning(
            "Storage video skipped: caption does not contain title/imdb. chat_id=%s message_id=%s caption=%r",
            message.chat.id,
            message.message_id,
            message.caption,
        )
        return

    media_type, file_id, file_unique_id = media
    save_telegram_video(
        content_type=parsed_caption.content_type,
        title=parsed_caption.title,
        year=parsed_caption.year,
        season=parsed_caption.season,
        episode=parsed_caption.episode,
        voiceover=parsed_caption.voiceover,
        imdb_id=parsed_caption.imdb_id,
        media_type=media_type,
        file_id=file_id,
        file_unique_id=file_unique_id,
        storage_chat_id=message.chat.id,
        message_id=message.message_id,
    )

    logger.info(
        "Storage video indexed: imdb_id=%s content_type=%s title=%s year=%s season=%s episode=%s voiceover=%s media_type=%s message_id=%s",
        parsed_caption.imdb_id,
        parsed_caption.content_type,
        parsed_caption.title,
        parsed_caption.year,
        parsed_caption.season,
        parsed_caption.episode,
        parsed_caption.voiceover,
        media_type,
        message.message_id,
    )
