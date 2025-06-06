import unittest
from unittest.mock import patch, MagicMock

from vidfetch_bot.video import Video, InvalidReason


class ValidVideoTestCase(unittest.TestCase):
    @patch("vidfetch_bot.video.YoutubeDL.extract_info")
    def setUp(self, mock_info):
        mock_info.return_value = {
            "title": "Valid Video Title",
            "description": "Valid video description",
            "duration": 133.4,
            "height": 480,
            "width": 360,
            "filesize": 9001,
        }
        self.video = Video("https://mock.example/video")

    def test_is_valid(self):
        self.assertIsInstance(self.video.is_valid, bool)
        self.assertTrue(self.video.is_valid)

    def test_title(self):
        self.assertIsInstance(self.video.title, str)
        self.assertEqual(self.video.title, "Valid Video Title")

    def test_description(self):
        self.assertIsInstance(self.video.description, str)
        self.assertEqual(self.video.description, "Valid video description")

    def test_duration(self):
        self.assertIsInstance(self.video.duration, int)
        self.assertEqual(self.video.duration, 133)

    def test_dimensions(self):
        self.assertIsInstance(self.video.dimensions, tuple)
        self.assertTupleEqual(self.video.dimensions, (480, 360))

    def test_filesize(self):
        self.assertIsInstance(self.video.filesize, int)
        self.assertEqual(self.video.filesize, 9001)

    def test_invalid_reason(self):
        self.assertIsNone(self.video.invalid_reason)

    def set_file_path(self, file_path: str):
        self.video.file_path = file_path

    @patch("vidfetch_bot.video.YoutubeDL.download")
    def test_download(self, mock_download):
        mock_post_hook = MagicMock()
        mock_post_hook.side_effect = self.set_file_path("mock_path")
        mock_download.side_effect = mock_post_hook
        with self.assertLogs("vidfetch_bot.video", "INFO") as cm:
            self.video.download()
        self.assertListEqual(cm.output, ["INFO:vidfetch_bot.video:Downloading video"])
        self.assertLogs(self.video.file_path, "mock_path")

    @patch("vidfetch_bot.video.os.remove")
    def test_delete(self, mock_remove):
        self.video.file_path = "mock_path"
        with self.assertLogs("vidfetch_bot.video", "INFO") as cm:
            self.video.delete()
        self.assertListEqual(cm.output, ["INFO:vidfetch_bot.video:Deleting 'mock_path'"])
        mock_remove.assert_called_with("mock_path")


class BigVideoTestCase(unittest.TestCase):
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
        self.assertListEqual(cm.output, ["WARNING:vidfetch_bot.video:Invalid video, won't download"])
        self.assertIsNone(self.video.file_path)

    def test_delete(self):
        with self.assertLogs("vidfetch_bot.video", "INFO") as cm:
            self.video.delete()
        self.assertListEqual(cm.output, ["WARNING:vidfetch_bot.video:No file to delete"])


class LongVideoTestCase(unittest.TestCase):
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
