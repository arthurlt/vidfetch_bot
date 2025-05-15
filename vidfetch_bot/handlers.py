import logging

from aiogram import Router, flags
from aiogram.enums import ChatAction, MessageEntityType
from aiogram.filters import CommandStart
from aiogram.types import FSInputFile, Message, ReactionTypeEmoji

from vidfetch_bot import utils
from vidfetch_bot.filters import EntityTypeFilter
from vidfetch_bot.video import InvalidReason, Video

handle = Router()

# TODO: support text_link type
@handle.message(EntityTypeFilter(MessageEntityType.URL))
@flags.chat_action(action=ChatAction.UPLOAD_VIDEO)
async def url_handler(message: Message):
    """"""
    log = logging.getLogger(__name__)
    if message.entities is None:
        return
    if message.text is None:
        return
    if message.from_user is None:
        return
    for entity in message.entities:
        log.debug(entity)
        url = utils.extract_entity(message.text, entity)
        log.info(f"'{url}' received from {message.from_user.username} in {message.chat.title or 'DM'}")

        # TODO: rework this
        async def send_error(error: str, emoji: str):
            reaction = ReactionTypeEmoji(emoji=emoji)
            await message.react([reaction], is_big=emoji in ["🍌", "🌭"])
            await message.reply(text=error)

        v = Video(url)
        # if not v.is_valid:
        #     pass
        v.download()

        match v.invalid_reason:
            case InvalidReason.FILE_TOO_BIG:
                await send_error("too big", "🍌")
                continue
            case InvalidReason.VIDEO_TOO_LONG:
                await send_error("too long", "🌭")
                continue
            case InvalidReason.DOWNLOAD_FAILED:
                await send_error("download failed", "🗿")
                continue
            case InvalidReason.UNSUPPORTED_URL:
                await send_error("unsupported url", "🤷")
                continue
            case _:
                if not v.file_path:
                    continue

                height, width = v.dimensions
                try:
                    await message.reply_video(
                        video=FSInputFile(path=v.file_path),
                        duration=v.duration,
                        width=width,
                        height=height,
                        caption=utils.generate_caption(v),
                        disable_notification=True,
                    )
                except Exception as e:
                    log.exception(f"Exception during answer_video: {e}")
                finally:
                    v.delete()

    # if failed:
    #     log.warning(f"URLs that failed: {failed}")
    #     if len(failed) == len(["url" in entity.type for entity in message.entities]):
    #         log.error("All provided URLs failed processing")
    #         return
    #     for v in failed:
    #         try:
    #             await message.answer(
    #                 text=f"There was an error processing this:\n{v.url}",
    #                 disable_notification=True,
    #                 disable_web_page_preview=False,
    #             )
    #         except Exception as e:
    #             log.exception(f"Exception during answer: {e}")


@handle.message(CommandStart())
async def command_start_handler(message: Message):
    """
    This handler receives messages with `/start` command
    """
    await message.answer("DM me your videos or add me to your group chats!")
