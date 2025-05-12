import logging
import re

from aiogram.types import User, Message, MessageEntity

from vidfetch_bot.video import Video


# TODO: shrink caption to be no more than 3 lines
def generate_caption(video: Video, user: User) -> str:
    """"""
    regex = re.compile(r"#\w+\s*")

    caption: str = ""

    if video.description is None:
        caption = video.title
    else:
        caption = video.description

    return f"<tg-spoiler>{regex.sub('', caption.splitlines()[0])}</tg-spoiler>"


def extract_entity(text: str, entity: MessageEntity) -> str:
    """"""
    return text[entity.offset : (entity.offset + entity.length)]
