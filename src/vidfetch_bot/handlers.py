import logging

from aiogram import Router, flags
from aiogram.enums import MessageEntityType
from aiogram.filters import CommandStart
from aiogram.types import FSInputFile, Message, ReactionTypeEmoji

from vidfetch_bot import utils
from vidfetch_bot.filters import EntityTypeFilter
from vidfetch_bot.video import InvalidReason, Video

handle = Router()

# TODO: support text_link type
#   looks like that then provides the url via the entity.url
@handle.message(EntityTypeFilter(MessageEntityType.URL))
@flags.chat_action(action="upload_video")
async def url_handler(message: Message):
    """ """
    if message.entities is None:
        return
    if message.text is None:
        return
    if message.from_user is None:
        return
    failed: list[Video] = []
    for entity in message.entities:
        logging.debug(entity)
        if entity.type != "url":
            logging.info("types.Message entity wasn't a url type")
            continue
        url = utils.get_substring(message.text, entity.offset, entity.length)
        logging.info(f"{url} received from {message.from_user.username} in {message.chat.title}")

        v = Video(url=url)

        v.download()

        async def send_error(error: str, emoji: str):
            reaction = ReactionTypeEmoji(emoji=emoji)
            failed.append(v)
            await message.react([reaction], is_big=emoji in ["🍌", "🌭"])
            await message.reply(text=error)

        # https://www.instagram.com/reel/DJNsth-Ifgq/?igsh=aGY4NDNlcHhydjF2

        match v.invalid_reason:
            case InvalidReason.FILE_TOO_BIG:
                # https://youtu.be/VQRLujxTm3c?si=v6WVehG9ZcPNlZID
                await send_error("too big", "🍌")
                continue
            case InvalidReason.VIDEO_TOO_LONG:
                # https://youtu.be/ctM2TIXDFQs?si=G17znpgX1IVJDrek
                await send_error("too long", "🌭")
                continue
            case InvalidReason.DOWNLOAD_FAILED:
                await send_error("download failed", "🗿")
                continue
            case InvalidReason.UNSUPPORTED_URL:
                # https://www.tiktok.com/t/ZTjDRMQjW
                await send_error("unsupported url", "🤷")
                continue

        if not v.file_path:
            continue

        height, width = v.dimensions
        try:
            await message.reply_video(
                video=FSInputFile(path=v.file_path),
                duration=v.duration,
                width=width,
                height=height,
                caption=utils.generate_caption(v, message.from_user),
                disable_notification=True,
            )
        except Exception as e:
            log.exception(f"Exception during answer_video: {e}")
            failed.append(v)
        finally:
            v.delete()
    if failed:
        log.warning(f"URLs that failed: {failed}")
        if len(failed) == len(["url" in entity.type for entity in message.entities]):
            log.error("All provided URLs failed processing")
            return
        for v in failed:
            try:
                await message.answer(
                    text=f"There was an error processing this:\n{v.url}",
                    disable_notification=True,
                    disable_web_page_preview=False,
                )
            except Exception as e:
                log.exception(f"Exception during answer: {e}")


@handle.message(CommandStart())
async def command_start_handler(message: Message):
    """
    This handler receives messages with `/start` command
    """
    await message.answer("DM me your videos or add me to your group chats!")
