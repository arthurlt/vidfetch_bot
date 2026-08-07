import json
import logging
import subprocess
import tempfile
from collections import Counter
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError, ExtractorError, UnsupportedError

logger = logging.getLogger(__name__)


class InvalidReason(Enum):
    DOWNLOAD_FAILED = auto()
    UNSUPPORTED_URL = auto()
    VIDEO_TOO_LONG = auto()
    FILE_TOO_BIG = auto()
    UNAUTHORIZED = auto()


@dataclass
class VideoDimensions:
    width: int
    height: int


class Video:
    max_duration = 600  # 10 minutes
    max_filesize = 50 * 1024 * 1024  # 50 mebibytes
    temp_file_dir = tempfile.gettempdir()
    common_opts = {
        "format": f"best[filesize<{max_filesize}] / best[filesize_approx<{max_filesize}] / bv*+ba / b",
        "format_sort": ["vcodec:avc", "res", "acodec:aac"],
        "max_filesize": max_filesize,
    }

    def __init__(self, url: str):
        self.url = url
        self.info = {}
        self.file_path: str | None = None
        self.invalid_reason = self.__validate()

    @property
    def is_valid(self) -> bool:
        return self.invalid_reason is None

    @property
    def title(self) -> str:
        if not self.info:
            raise KeyError
        return self.info["title"]

    @property
    def description(self) -> str | None:
        if not self.info:
            raise KeyError
        return self.info.get("description")

    @property
    def duration(self) -> int:
        if not self.info:
            raise KeyError
        return int(self.info["duration"])

    @property
    def dimensions(self) -> VideoDimensions:
        if not self.info:
            raise KeyError
        try:
            if not self.file_path:
                raise KeyError
            probe_output = subprocess.check_output(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-select_streams",
                    "v",
                    "-show_streams",
                    "-print_format",
                    "json",
                    self.file_path,
                ]
            )
            probe_data = json.loads(probe_output)
            return VideoDimensions(probe_data["streams"][0]["width"], probe_data["streams"][0]["height"])
        except Exception as e:
            logger.warning(f"Failed to use ffprobe: {e}")
            if not self.info.get("width"):
                self.info["width"] = 0
            if not self.info.get("height"):
                self.info["height"] = 0
            # Workaround when the format ytdlp selects has the width and height swapped for some reason
            ratios = [format.get("aspect_ratio") for format in self.info["formats"]]
            if Counter(ratios)[self.info["aspect_ratio"]] == 1 and len(ratios) >= 3:
                return VideoDimensions(self.info["height"], self.info["width"])
            return VideoDimensions(self.info["width"], self.info["height"])

    @property
    def filesize(self) -> int | None:
        if not self.info:
            raise KeyError
        if self.info.get("filesize"):
            return int(self.info["filesize"])
        if self.info.get("filesize_approx"):
            return int(self.info["filesize_approx"])
        return None

    def __validate(self) -> InvalidReason | None:
        if not self.info:
            try:
                logger.debug(f"Retrieving info for '{self.url}'")
                opts = self.common_opts | {"logger": logger}
                with YoutubeDL(opts) as ydl:
                    self.info = ydl.extract_info(self.url, download=False)
            except DownloadError as e:
                logger.debug(e.exc_info)
                match e.exc_info:
                    case (_, UnsupportedError(), *_):
                        return InvalidReason.UNSUPPORTED_URL
                    case (_, ExtractorError() as ee, *_) if "--cookies" in ee.msg:
                        return InvalidReason.UNAUTHORIZED
                    case _:
                        return InvalidReason.DOWNLOAD_FAILED

        if self.duration > self.max_duration:
            logger.warning(f"'{self.title}' is greater than {self.max_duration} seconds")
            return InvalidReason.VIDEO_TOO_LONG

        if self.filesize and self.filesize > self.max_filesize:
            logger.warning(f"'{self.title}' is bigger than {self.max_filesize} bytes")
            return InvalidReason.FILE_TOO_BIG
        return None

    def __post_hook(self, filename: str):
        logger.info(f"Downloaded video to '{filename}'")
        self.__actual_filesize = Path(filename).stat().st_size
        if self.__actual_filesize > self.max_filesize:
            self.invalid_reason = InvalidReason.FILE_TOO_BIG
            logger.warning(f"'{self.title}' is bigger than {self.max_filesize} bytes")
            self.delete()
            return
        self.file_path = filename

    def download(self):
        if not self.is_valid:
            logger.warning("Invalid video, won't download")
            return
        logger.info("Downloading video")
        opts = self.common_opts | {
            "concurrent_fragment_downloads": 8,
            "logger": logger,
            "noprogress": True,
            "paths": {"home": self.temp_file_dir, "temp": self.temp_file_dir},
            "post_hooks": [self.__post_hook],
            "restrictfilenames": True,
        }
        with YoutubeDL(opts) as ydl:
            ydl.download(self.url)

    def delete(self):
        if not self.file_path:
            logger.warning("No file to delete")
            return
        logger.info(f"Deleting '{self.file_path}'")
        Path(self.file_path).unlink()
