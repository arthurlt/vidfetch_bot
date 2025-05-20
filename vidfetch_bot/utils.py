import logging
import re

from aiogram.methods.send_video import SendVideo
from aiogram.methods.set_message_reaction import SetMessageReaction
from aiogram.types import FSInputFile, Message, ReactionTypeEmoji

from vidfetch_bot.video import InvalidReason, Video


def generate_caption(video: Video) -> str:
    # use video title if no description
    caption: str = video.description or video.title

    # remove extra lines
    caption = caption.splitlines()[0] or caption

    # remove all hashtags
    caption = re.sub(r"#\w+\s*", "", caption)

    # limit to 8 words
    if len(caption.split()) > 8:
        caption = " ".join(caption.split()[0:8]) + " ..."

    # remove leading or trailing whitespace
    caption = caption.strip()

    return f"<tg-spoiler>{caption}</tg-spoiler>"


def generate_response(message: Message, video: Video) -> SendVideo | SetMessageReaction:
    log = logging.getLogger(__name__)
    match video.invalid_reason:
        case InvalidReason.FILE_TOO_BIG:
            return message.react(reaction=[ReactionTypeEmoji(emoji="🐳")])
        case InvalidReason.VIDEO_TOO_LONG:
            return message.react(reaction=[ReactionTypeEmoji(emoji="🤨")])
        case InvalidReason.UNSUPPORTED_URL:
            return message.react(reaction=[ReactionTypeEmoji(emoji="🤷")])
        case InvalidReason.DOWNLOAD_FAILED:
            return message.react(reaction=[ReactionTypeEmoji(emoji="😢")])
        case InvalidReason.UNAUTHORIZED:
            return message.react(reaction=[ReactionTypeEmoji(emoji="🙈")])
        case None:
            if not video.file_path:
                raise FileNotFoundError(f"No file path for {video.title}")
            log.info("Sending video")
            height, width = video.dimensions
            return message.reply_video(
                video=FSInputFile(video.file_path),
                duration=video.duration,
                height=height,
                width=width,
                caption=generate_caption(video),
                disable_notification=True,
            )
