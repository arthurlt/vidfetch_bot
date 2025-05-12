import re

from aiogram.types import MessageEntity

from vidfetch_bot.video import Video


# TODO: shrink caption to be no more than 3 lines
def generate_caption(video: Video) -> str:
    """"""

    # use video title if no description
    caption: str = video.description or video.title

    # remove extra lines
    caption = caption.splitlines()[0] or caption

    # remove all hashtags
    caption = re.sub(r"#\w+\s*", "", caption)

    # remove 
    if len(caption.split()) > 8:
        caption = " ".join(caption.split()[0:8]) + " ..."

    return f"<tg-spoiler>{caption}</tg-spoiler>"


def extract_entity(text: str, entity: MessageEntity) -> str:
    """"""
    return text[entity.offset : (entity.offset + entity.length)]
