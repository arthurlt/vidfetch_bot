import asyncio
import logging
import sys
import re
import os
import json

from enum import Enum
from shutil import rmtree
from aiogram import Bot, Dispatcher, flags
from aiogram.enums import ParseMode
from aiogram.types import Message, FSInputFile
from aiogram.filters import Filter
from aiogram.utils.chat_action import ChatActionMiddleware

# All handlers should be attached to the Router (or Dispatcher)
dp = Dispatcher()
dp.message.middleware(ChatActionMiddleware())

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

def generate_caption(info):
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
    caption = regex.sub("", caption)

    return caption

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

@dp.message(EntityTypeFilter('url'))
@flags.chat_action("upload_video")
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

        simulate_result = await run_yt_dlp(video_url=url, simulate=True ,dir=download_dir)
        if simulate_result.returncode != 0:
            print(f"yt-dlp failed to process {url}\n{simulate_result.stderr}")
            continue

        download_result = await run_yt_dlp(video_url=url,dir=download_dir)
        if download_result.returncode != 0:
            print(f"yt-dlp failed to download {url}\n{download_result.stderr}")
            continue

        # TODO: make sure the video file is under 50mb
        try:
            print(f"{download_dir}/video.info.json")
            with open(f"{download_dir}/video.info.json") as j:
                video_info = json.load(j)
        except:
            print(f"Failed to open the JSON")
            continue

        try:
            await message.reply_video(
                video=FSInputFile(path=f"{download_dir}/video.mp4"),
                duration=int(video_info['duration']),
                width=video_info['width'],
                height=video_info['height'],
                caption=generate_caption(video_info),
                #thumbnail:f"{download_dir}/{yt_dlp_file.THUMBNAIL}",
                #thumbnail=video_info['thumbnail'],
                disable_notification=True
            )
        except:
            print(f"Failed sending video reply")
            continue
        finally:
            try:
                rmtree(download_dir)
            except:
                print(f"Failed to delete directory")
                continue



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