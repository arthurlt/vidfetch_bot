import logging
import os.path
import tempfile
from enum import Enum, auto

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError, ExtractorError, UnsupportedError


class InvalidReason(Enum):
    DOWNLOAD_FAILED = auto()
    UNSUPPORTED_URL = auto()
    VIDEO_TOO_LONG = auto()
    FILE_TOO_BIG = auto()
    UNAUTHORIZED = auto()


class Video:
    log: logging.Logger
    max_duration = 600  # 10 minutes
    max_filesize = 50 * 1024 * 1024  # 50 mebibytes
    temp_file_dir = tempfile.gettempdir()
    common_opts = {
        "format": f"best[filesize<{max_filesize}] / best[filesize_approx<{max_filesize}] / bv*+ba / b",
        "format_sort": ["vcodec:avc", "res", "acodec:aac"],
        "max_filesize": max_filesize,
    }

    def __init__(self, url: str):
        self.log = logging.getLogger(__name__)
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
    def dimensions(self) -> tuple[int, int]:
        if not self.info:
            raise KeyError
        return self.info["height"], self.info["width"]

    @property
    def filesize(self) -> int | None:
        if not self.info:
            raise KeyError
        if self.info.get("filesize"):
            return int(self.info["filesize"])
        if self.info.get("filesize_approx"):
            return int(self.info["filesize_approx"])

    def __validate(self) -> InvalidReason | None:
        if not self.info:
            try:
                self.log.debug(f"Retrieving info for '{self.url}'")
                opts = self.common_opts | {"logger": self.log}
                with YoutubeDL(opts) as ydl:
                    self.info = ydl.extract_info(self.url, download=False)
            except DownloadError as e:
                self.log.debug(e.exc_info)
                match e.exc_info:
                    case (_, UnsupportedError(), *_):
                        return InvalidReason.UNSUPPORTED_URL
                    case (_, ExtractorError() as ee, *_) if "--cookies" in ee.msg:
                        return InvalidReason.UNAUTHORIZED
                    case _:
                        return InvalidReason.DOWNLOAD_FAILED

        if self.duration > self.max_duration:
            self.log.warning(f"'{self.title}' is greater than {self.max_duration} seconds")
            return InvalidReason.VIDEO_TOO_LONG

        if self.filesize and self.filesize > self.max_filesize:
            self.log.warning(f"'{self.title}' is bigger than {self.max_filesize} bytes")
            return InvalidReason.FILE_TOO_BIG

    def __post_hook(self, filename: str):
        self.log.info(f"Downloaded video to '{filename}'")
        self.__actual_filesize = os.path.getsize(filename)
        if self.__actual_filesize > self.max_filesize:
            self.invalid_reason = InvalidReason.FILE_TOO_BIG
            self.log.warning(f"'{self.title}' is bigger than {self.max_filesize} bytes")
            self.delete()
            return
        self.file_path = filename

    def download(self):
        if not self.is_valid:
            self.log.warning("Invalid video, won't download")
            return
        self.log.info("Downloading video")
        opts = self.common_opts | {
            "concurrent_fragment_downloads": 8,
            "logger": self.log,
            "noprogress": True,
            "paths": {"home": self.temp_file_dir, "temp": self.temp_file_dir},
            "post_hooks": [self.__post_hook],
            "restrictfilenames": True,
        }
        with YoutubeDL(opts) as ydl:
            ydl.download(self.url)

    def delete(self):
        if not self.file_path:
            self.log.warning("No file to delete")
            return
        self.log.info(f"Deleting '{self.file_path}'")
        os.remove(self.file_path)
