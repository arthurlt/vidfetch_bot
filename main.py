import asyncio
import logging
import sys
import re
import os
import json

from enum import Enum
from pathlib import Path
from shutil import rmtree

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

def validate_string(string: str) -> bool:
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
def generate_caption(info: dict, user: types.User, reply=False) -> str:
    """
    Generates a caption from a dictionary of information.

    Args:
      info: A dictionary containing the following keys:
        - title: The title of the content.
        - description: The description of the content.

    Returns:
      A string containing the caption without hashtags.
    """
    # Define the regular expression to match hashtags
    regex = re.compile(r"#\w+\s*")

    # Initialize the caption variable
    caption = ""

    # Check if the description is valid
    if not validate_string(info["description"]):
        # Use the title if no valid description is provided
        caption = info["title"]
    else:
        # Use the description if available
        caption = info["description"]

    if reply:
        return regex.sub('', caption)

    template = "<b><a href='tg://user?id={}'>{}</a> <a href='{}'>sent ↑</a></b>\n{}"

    return template.format(
        user.id,
        user.first_name,
        info["webpage_url"],
        regex.sub('', caption)
    )

async def has_delete_permissions(message: types.Message) -> bool:
    # Something went wrong
    if message.bot is None:
        return False

    if message.chat.type == "private":
        return True

    member = await message.bot.get_chat_member(message.chat.id, message.bot.id)

    if isinstance(member, types.ChatMemberAdministrator) and member.can_delete_messages:
        return True
    else:
        return False

# def launch_yt_dlp(dir="/tmp", extra_opts={}):
#     if not os.path.exists(dir):
#         try:
#             os.makedirs(dir)
#         except Exception as e:
#             print(f"Exception during directory creation: {e}")
#             print("Setting dir to /tmp as fallback")
#             dir = "/tmp"
#     ydl_opts = {
#         'final_ext': 'mp4',
#         'fragment_retries': 10,
#         'ignoreerrors': 'only_download',
#         'paths': {'home': dir},
#         'postprocessors': [
#             {'key': 'FFmpegVideoRemuxer', 'preferedformat': 'mp4'}
#         ],
#         'restrictfilenames': True,
#         'retries': 10,
#         'trim_file_name': 8
#     }
#     if extra_opts:
#         ydl_opts.
#     with YoutubeDL(ydl_opts) as ydl:
#         return ydl


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
        #"--write-thumbnail",
        #"--convert-thumbnails",
        # "jpg",
        "--format",
        "bestvideo*[height<=?1080][filesize<40M]+bestaudio/best",
        #"--format-sort",
        #"hasvid,hasaud,quality",
        "--max-filesize",
        "50M",
        "--recode-video",
        "mp4",
        "--output",
        "video.%(ext)s",
        video_url,
    ]
    # Add simulate flag if requested
    if simulate:
        args.append("--simulate")
    # Create the download directory if it does not exist
    if not os.path.exists(dir):
        try:
            os.makedirs(dir)
        except Exception as e:
            print(f"Exception during directory creation: {e}")
            print("Setting dir to /tmp as fallback")
            dir = "/tmp"
    # Run yt-dlp asynchronously
    process = await asyncio.create_subprocess_exec(
        "yt-dlp", *args, cwd=dir
    )
    await process.wait()
    # TODO: also return paths for files
    return process

async def try_delete(message: types.Message) -> bool:
    try:
        await message.delete()
    except Exception as e:
        print(f"Exception during delete: {e}")
        return False
    else:
        return True

# TODO: support text_link type
#   looks like that then provides the url via the entity.url
# TODO: if we're able to send the video delete the original message
#   make sure the OP gets credit
#   also make the caption link to the video
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
    for entity in message.entities:
        print(entity)
        url = get_substring(message.text, entity.offset, entity.length)
        download_dir = f"/tmp/yt-dlp-{message.message_id}-{hash(url)}";
        video_file = Path(f"{download_dir}/video.mp4")
        print(f"{url} received from {message.from_user.username} in {message.chat.title}")

        download_result = await run_yt_dlp(video_url=url,dir=download_dir)
        if download_result.returncode != 0:
            print(f"yt-dlp failed to download {url}\n{download_result.stderr}")
            continue

        try:
            with open(f"{download_dir}/video.info.json") as j:
                video_info = json.load(j)
        except Exception as e:
            print(f"Exception during opening JSON: {e}")
            continue

        # TODO: make this a try/except block
        if not video_file.is_file():
            print(f"video_file is missing")
            continue

        # TODO: upload video file and respond separately
        try:
            await message.answer_video(
                video=types.FSInputFile(path=video_file),
                duration=int(video_info['duration']),
                width=video_info['width'],
                height=video_info['height'],
                # TODO: send bool for reply to get different caption when replying
                caption=generate_caption(video_info, message.from_user),
                disable_notification=True,
                reply_to_message_id=None if await try_delete(message) else message.message_id
            )
        except Exception as e:
            print(f"Exception during answer_video: {e}")
            await message.reply(
                text="I'm sorry, there was an error... \n" + message.text,
                disable_web_page_preview=False,
                allow_sending_without_reply=True
            )
        finally:
            rmtree(download_dir)

@dp.message(CommandStart())
async def command_start_handler(message: types.Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    await message.answer(f"DM me your videos, or add me to your group chats!")

@dp.message(Command("test"))
async def command_test_handler(message: types.Message) -> None:
    if await has_delete_permissions(message):
        await message.answer("can delete messages")
    else:
        await message.answer("can't delete messages")

async def main() -> None:
    """
    """
    # Bot token can be obtained via https://t.me/BotFather
    TOKEN = os.getenv("BOT_TOKEN")

    if not validate_string(TOKEN):
        raise ValueError('ENV not set')

    # Initialize Bot instance with a default parse mode which will be passed to all API calls
    bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())