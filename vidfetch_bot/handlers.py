import logging

from aiogram import Router, flags
from aiogram.enums import ChatAction, MessageEntityType
from aiogram.filters import CommandStart
from aiogram.types import Message

from vidfetch_bot import utils
from vidfetch_bot.filters import EntityTypeFilter
from vidfetch_bot.video import Video

handle = Router()


# TODO: support text_link type
@handle.message(EntityTypeFilter(MessageEntityType.URL))
@flags.chat_action(action=ChatAction.UPLOAD_VIDEO)
async def url_handler(message: Message):
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

        video = Video(url)
        if video.is_valid:
            video.download()

        try:
            await utils.generate_response(message, video)
        finally:
            if video.file_path:
                video.delete()


@handle.message(CommandStart())
async def command_start_handler(message: Message):
    """This handler receives messages with `/start` command"""
    await message.answer("DM me your videos or add me to your group chats!")
