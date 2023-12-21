import asyncio
import logging
import sys
import re
import os
import json

from enum import Enum
from pathlib import Path
from shutil import rmtree
from typing import Any

from aiogram import Bot, Dispatcher, flags, types
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart, Filter
from aiogram.utils.chat_action import ChatActionMiddleware

# All handlers should be attached to the Router (or Dispatcher)
dp = Dispatcher()
dp.message.middleware(ChatActionMiddleware())

fifty_mb = 52428800


class yt_dlp_file(Enum):
    VIDEO = 'video.mp4'
    THUMBNAIL = 'video.jpg'
    JSON = 'video.info.json'


class EntityTypeFilter(Filter):
    """
    """

    def __init__(self, filter_type: str) -> None:
        self.filter_type = filter_type

    async def __call__(self, message: types.Message) -> bool:
        if message.entities is None:
            return False
        else:
            print(message.entities)
            return any([self.filter_type in entity.type for entity in message.entities])


def validate_string(string: str | None) -> bool:
    """
    Checks if a string is not None and not empty.

    Args:
        string: The string to validate.

    Returns:
        True if the string is not None and not empty, False otherwise.
    """
    return string is not None and len(string) > 0


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
def generate_caption(info: dict[str, Any], user: types.User, reply=False) -> str:
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

    caption = ""

    # dict.get() doesn't throw an exception if the key is missing
    if not validate_string(info.get("description")):
        caption = info["title"]
    else:
        caption = info["description"]

    if reply:
        return f"<tg-spoiler>{regex.sub('', caption)}</tg-spoiler>"

    template = "<b><a href='tg://user?id={}'>{}</a> <a href='{}'>sent ↑</a></b>\n<tg-spoiler>{}</tg-spoiler>"

    return template.format(
        user.id,
        user.first_name,
        info["webpage_url"],
        regex.sub('', caption)
    )


async def has_delete_permissions(message: types.Message) -> bool:
    """
    """
    if message.bot is None:
        return False

    if message.chat.type == "private":
        return True

    member = await message.bot.get_chat_member(message.chat.id, message.bot.id)

    if isinstance(member, types.ChatMemberAdministrator) and member.can_delete_messages:
        return True
    else:
        return False


async def run_yt_dlp(video_url: str, simulate=False, dir="/tmp") -> asyncio.subprocess.Process:
    """
    Downloads a YouTube video using yt-dlp.
    Args:
        video_url: The URL of the video to download.
        simulate: (Optional) Whether to simulate the download without actually downloading the video.
        dir: (Optional) The directory to download the video to.

    Returns:
        A subprocess.CompletedProcess instance containing the process results.
    """
    # Define yt-dlp arguments
    args = [
        "--write-info-json",
        # format conversion is failing: https://github.com/yt-dlp/yt-dlp/issues/6866
        # "--write-thumbnail",
        # "--convert-thumbnails",
        # "jpg",
        # "--format",
        # "bestvideo*[filesize<?30M]+bestaudio*/best[filesize<?40M]",
        "--format-sort",
        "filesize:40M",
        "--merge-output-format",
        "mp4",
        "--recode-video",
        "mp4",
        "--max-filesize",
        "50M",
        "--restrict-filenames",
        "--trim-filenames",
        "10",
        "--output",
        "video.%(ext)s",
        video_url,
    ]
    if simulate:
        args.append("--simulate")
    if not os.path.exists(dir):
        try:
            os.makedirs(dir)
        except Exception as e:
            print(f"Exception during directory creation: {e}")
            print("Setting dir to /tmp as fallback")
            dir = "/tmp"
    process = await asyncio.create_subprocess_exec(
        "yt-dlp", *args, cwd=dir
    )
    await process.wait()
    # TODO: also return paths for files
    return process


# TODO: support text_link type
#   looks like that then provides the url via the entity.url
# TODO: specifically handle slideshow tiktoks
@dp.message(EntityTypeFilter('url'))
@flags.chat_action(action="upload_video")
async def url_handler(message: types.Message) -> None:
    """
    """
    if message.entities is None:
        return
    if message.text is None:
        return
    if message.from_user is None:
        return
    can_delete = await has_delete_permissions(message)
    failed_urls = []
    for entity in message.entities:
        print(entity)
        if entity.type != "url":
            print(f"Message entity wasn't a url type")
            continue
        url = get_substring(message.text, entity.offset, entity.length)
        download_dir = f"/tmp/yt-dlp-{message.message_id}-{hash(url)}"
        video_file = Path(f"{download_dir}/video.mp4")
        print(f"{url} received from {message.from_user.username} in {message.chat.title}")

        download_result = await run_yt_dlp(video_url=url, dir=download_dir)
        if download_result.returncode != 0:
            print(f"yt-dlp failed to download {url}\n{download_result.stderr}")
            failed_urls.append(url)
            continue

        try:
            with open(f"{download_dir}/video.info.json") as j:
                video_info = json.load(j)
        except Exception as e:
            print(f"Exception during opening JSON: {e}")
            failed_urls.append(url)
            continue

        # TODO: make this a try/except block
        if not video_file.is_file():
            print(f"video_file is missing")
            failed_urls.append(url)
            continue

        # TODO: upload video file and respond separately
        try:
            await message.answer_video(
                video=types.FSInputFile(path=video_file),
                duration=int(video_info['duration']),
                width=video_info['width'],
                height=video_info['height'],
                caption=generate_caption(
                    video_info, message.from_user, reply=not can_delete),
                disable_notification=True,
                reply_to_message_id=None if can_delete else message.message_id
            )
        except Exception as e:
            print(f"Exception during answer_video: {e}")
            failed_urls.append(url)
            continue
        finally:
            rmtree(download_dir)
    if failed_urls:
        print(f"URLs that failed: {failed_urls}")
        if len(failed_urls) == len([["url" in entity.type for entity in message.entities]]):
            print(f"All provided URLs failed processing")
            return
        for url in failed_urls:
            try:
                await message.answer(
                    text=f"There was an error processing this:\n{url}",
                    disable_notification=True,
                    disable_web_page_preview=False
                )
            except Exception as e:
                print(f"Exception during answer: {e}")
    try:
        await message.delete()
    except Exception as e:
        print(f"Exception during delete: {e}")


@dp.message(CommandStart())
async def command_start_handler(message: types.Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    await message.answer(f"DM me your videos, or add me to your group chats!")


@dp.message(Command("test"))
async def command_test_handler(message: types.Message) -> None:
    # Put stuff you're testing in here
    pass


async def main() -> None:
    # Bot token can be obtained via https://t.me/BotFather
    TOKEN = os.getenv("BOT_TOKEN")

    if not validate_string(TOKEN):
        raise ValueError('ENV not set')

    # Initialize Bot instance with a default parse mode which will be passed to all API calls
    bot = Bot(TOKEN, parse_mode=ParseMode.HTML)  # pyright: ignore
    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
