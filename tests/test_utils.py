import unittest
from unittest.mock import MagicMock

# from aiogram.methods.send_video import SendVideo

from vidfetch_bot import utils


class GenerateCaptionTestCases(unittest.TestCase):
    def test_short_description(self):
        video = MagicMock()
        video.description = "A short mock description"
        expected = "<tg-spoiler>A short mock description</tg-spoiler>"
        actual = utils.generate_caption(video)
        self.assertIsInstance(actual, str)
        self.assertEqual(expected, actual)

    def test_no_description(self):
        video = MagicMock()
        video.description = None
        video.title = "Mock Title"
        expected = "<tg-spoiler>Mock Title</tg-spoiler>"
        actual = utils.generate_caption(video)
        self.assertIsInstance(actual, str)
        self.assertEqual(expected, actual)

    def test_hashtag_removal(self):
        video = MagicMock()
        video.description = "A description with multiple hashtags #test #unittest #python #telegram"
        expected = "<tg-spoiler>A description with multiple hashtags</tg-spoiler>"
        actual = utils.generate_caption(video)
        self.assertIsInstance(actual, str)
        self.assertEqual(expected, actual)

    def test_8_word_limit(self):
        video = MagicMock()
        video.description = "I promise you that this description has eleven words in total"
        expected = "<tg-spoiler>I promise you that this description has eleven ...</tg-spoiler>"
        actual = utils.generate_caption(video)
        self.assertIsInstance(actual, str)
        self.assertEqual(expected, actual)

# TODO: test extract_entity and generate_response functions
