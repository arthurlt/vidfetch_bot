import unittest
from unittest.mock import patch

from vidfetch_bot.video import Video, InvalidReason


class ValidVideoTestCase(unittest.TestCase):
    @patch("vidfetch_bot.video.YoutubeDL.extract_info")
    def setUp(self, mock_info):
        mock_info.return_value = {
            "title": "Long Video Title",
            "description": "Long video description",
            "duration": 601,
            "height": 480,
            "width": 360,
            "filesize": 9001,
        }
        with self.assertLogs("vidfetch_bot.video", "INFO"):
            self.video = Video("https://mock.example/video")

    def test_is_valid(self):
        self.assertIsInstance(self.video.is_valid, bool)
        self.assertFalse(self.video.is_valid)

    def test_title(self):
        self.assertIsInstance(self.video.title, str)
        self.assertEqual(self.video.title, "Long Video Title")

    def test_description(self):
        self.assertIsInstance(self.video.description, str)
        self.assertEqual(self.video.description, "Long video description")

    def test_duration(self):
        self.assertIsInstance(self.video.duration, int)
        self.assertEqual(self.video.duration, 601)

    def test_dimensions(self):
        self.assertIsInstance(self.video.dimensions, tuple)
        self.assertTupleEqual(self.video.dimensions, (480, 360))

    def test_filesize(self):
        self.assertIsInstance(self.video.filesize, int)
        self.assertEqual(self.video.filesize, 9001)

    def test_invalid_reason(self):
        self.assertIsInstance(self.video.invalid_reason, InvalidReason)
        self.assertEqual(self.video.invalid_reason, InvalidReason.VIDEO_TOO_LONG)

    def test_download(self):
        with self.assertLogs("vidfetch_bot.video", "INFO") as cm:
            self.video.download()
        self.assertListEqual(cm.output, ["WARNING:vidfetch_bot.video:Invalid video, won't download"])
        self.assertIsNone(self.video.file_path)

    def test_delete(self):
        with self.assertLogs("vidfetch_bot.video", "INFO") as cm:
            self.video.delete()
        self.assertListEqual(cm.output, ["WARNING:vidfetch_bot.video:No file to delete"])
