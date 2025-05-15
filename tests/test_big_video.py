import unittest
from unittest.mock import patch

from vidfetch_bot.video import Video, InvalidReason


class ValidVideoTestCase(unittest.TestCase):
    @patch("vidfetch_bot.video.YoutubeDL.extract_info")
    def setUp(self, mock_info):
        mock_info.return_value = {
            "title": "Big Video Title",
            "description": "Big video description",
            "duration": 133.4,
            "height": 480,
            "width": 360,
            "filesize": 52428801,
        }
        with self.assertLogs("vidfetch_bot.video", "INFO"):
            self.video = Video("https://mock.example/video")

    def test_is_valid(self):
        self.assertIsInstance(self.video.is_valid, bool)
        self.assertFalse(self.video.is_valid)

    def test_title(self):
        self.assertIsInstance(self.video.title, str)
        self.assertEqual(self.video.title, "Big Video Title")

    def test_description(self):
        self.assertIsInstance(self.video.description, str)
        self.assertEqual(self.video.description, "Big video description")

    def test_duration(self):
        self.assertIsInstance(self.video.duration, int)
        self.assertEqual(self.video.duration, 133)

    def test_dimensions(self):
        self.assertIsInstance(self.video.dimensions, tuple)
        self.assertTupleEqual(self.video.dimensions, (480, 360))

    def test_filesize(self):
        self.assertIsInstance(self.video.filesize, int)
        self.assertEqual(self.video.filesize, 52428801)

    def test_invalid_reason(self):
        self.assertIsInstance(self.video.invalid_reason, InvalidReason)
        self.assertEqual(self.video.invalid_reason, InvalidReason.FILE_TOO_BIG)

    def test_download(self):
        with self.assertLogs("vidfetch_bot.video", "INFO") as cm:
            self.video.download()
        self.assertListEqual(cm.output, ["ERROR:vidfetch_bot.video:Invalid video, won't download"])
        self.assertIsNone(self.video.file_path)

    def test_delete(self):
        with self.assertLogs("vidfetch_bot.video", "INFO") as cm:
            self.video.delete()
        self.assertListEqual(cm.output, ["WARNING:vidfetch_bot.video:No file to delete"])
