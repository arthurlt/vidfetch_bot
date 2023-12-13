import asyncio
import logging
import sys
import re
import os
import json

from enum import Enum
from shutil import rmtree
from typing import Text

from aiogram import Bot, Dispatcher, flags
from aiogram.enums import ParseMode
from aiogram.methods.delete_message import DeleteMessage
from aiogram.methods.send_message import SendMessage
from aiogram.types import Message, FSInputFile, video
from aiogram.filters import Filter
from aiogram.utils.formatting import Text
from aiogram.utils.markdown import hbold, hlink
from aiogram.utils.chat_action import ChatActionMiddleware

# All handlers should be attached to the Router (or Dispatcher)
dp = Dispatcher()
dp.message.middleware(ChatActionMiddleware())

fifty_mb = 52428800

class yt_dlp_file(Enum):
    VIDEO = 'video.mp4'
    THUMBNAIL = 'video.jpg'
    JSON = 'video.info.json'

def validate_string(string):
    """
    Checks if a string is not None and not empty.

    Args:
      string: The string to validate.

    Returns:
      True if the string is not None and not empty, False otherwise.
    """
    return string is not None and len(string) > 0

def get_substring(string, offset, length):
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
def generate_caption(info, user):
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
    if not validate_string(info.get("description")):
        # Use the title if no valid description is provided
        caption = info["title"]
    else:
        # Use the description if available
        caption = info["description"]

    # Remove hashtags from the caption
    caption = f"<b><a href='tg://user?id={user.id}'>{user.first_name}</a> sent ↑\nCaption:\n</b>{regex.sub('', caption)}"

    return caption


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


async def run_yt_dlp(video_url, simulate=False, dir="/tmp"):
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
        "--remux-video",
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
    return process

class EntityTypeFilter(Filter):
    """
    """
    def __init__(self, filter_type: str) -> None:
        self.filter_type = filter_type

    async def __call__(self, message: Message) -> bool:
        if message.entities is None:
            return False
        else:
            print(message.entities)
            return any([self.filter_type in entity.type for entity in message.entities])

# TODO: support text_link type
#   looks like that then provides the url via the entity.url

# TODO: if we're able to send the video delete the original message
#   make sure the OP gets credit
#   also make the caption link to the video
# TODO: specifically handle slideshow tiktoks
@dp.message(EntityTypeFilter('url'))
@flags.chat_action(initial_sleep=2, action="upload_video", interval=2)
async def url_handler(message: Message) -> None:
    """
    """
    if message.entities is None:
        return None
    if message.text is None:
        return None
    if message.from_user is None:
        return None
    for entity in message.entities:
        print(entity)
        url = get_substring(message.text, entity.offset, entity.length)
        download_dir = f"/tmp/yt-dlp-{message.message_id}-{hash(url)}";
        print(f"{url} received from {message.from_user.username} in {message.chat.title}")

        simulate_result = await run_yt_dlp(video_url=url,simulate=True,dir=download_dir)
        if simulate_result.returncode != 0:
            print(f"yt-dlp failed to process {url}\n{simulate_result.stderr}")
            continue

        download_result = await run_yt_dlp(video_url=url,dir=download_dir)
        if download_result.returncode != 0:
            print(f"yt-dlp failed to download {url}\n{download_result.stderr}")
            continue

        try:
            print(f"{download_dir}/video.info.json")
            with open(f"{download_dir}/video.info.json") as j:
                video_info = json.load(j)
        except:
            print(f"Failed to open the JSON")
            continue

        try:
            video_size = os.path.getsize(f"{download_dir}/video.mp4")
        except:
            print(f"Failed to open the video")
            continue

        # TODO: implement way to shrink video size
        # TODO: determine video size before downloading
        if not video_size < fifty_mb:
            await message.reply(
                f"Video is larger that 50MB limit",
                disable_notification=True
            )
            continue

        # TODO: upload file and send message separately?
        try:
            await message.answer_video(
                video=FSInputFile(path=f"{download_dir}/video.mp4"),
                duration=int(video_info['duration']),
                width=video_info['width'],
                height=video_info['height'],
                caption=generate_caption(video_info, message.from_user),
                disable_notification=True
            )
        except:
            print(f"Failed sending video reply")
            raise
            continue
        finally:
            try:
                rmtree(download_dir)
            except:
                print(f"Failed to delete directory")
                continue

        # TODO: change behavior depending on if admin rights in chat
        await message.delete()



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