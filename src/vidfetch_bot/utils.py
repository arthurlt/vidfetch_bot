import re

from aiogram import types

from vidfetch_bot.video import Video


def get_substring(string: str, offset: int, length: int) -> str:
    """
    Extracts a substring from a string based on offset and length.

    Args:
        string: The string to extract from.
        offset: The starting position of the substring.
        length: The length of the substring.

    Returns:
        The extracted substring.
    """
    if offset < 0 or offset >= len(string):
        raise ValueError("Offset is out of bounds")
    end_index = min(offset + length, len(string))
    return string[offset:end_index]


# TODO: shrink caption to be no more than 3 lines
def generate_caption(video: Video, user: types.User) -> str:
    """
    Generates a caption from a dictionary of information.

    Args:
        info: A dictionary containing the following keys:
        - title: The title of the content.
        - description: The description of the content.

    Returns:
        A string containing the caption without hashtags.
    """
    regex = re.compile(r"#\w+\s*")

    caption: str = ""

    # dict.get() doesn't throw an exception if the key is missing
    if video.description is None:
        caption = video.title
    else:
        caption = video.description

    return f"<tg-spoiler>{regex.sub('', caption.splitlines()[0])}</tg-spoiler>"

def video_reply():
    pass