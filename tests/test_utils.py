import unittest
from unittest.mock import MagicMock, create_autospec

# from aiogram.methods.send_video import SendVideo
# from aiogram.methods.set_message_reaction import SetMessageReaction
from aiogram.types import Message, ReactionTypeEmoji

from vidfetch_bot import utils
from vidfetch_bot.video import InvalidReason


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


class GenerateResponseTestCases(unittest.TestCase):
    def test_too_big_reaction(self):
        video = MagicMock()
        video.invalid_reason = InvalidReason.FILE_TOO_BIG
        message = create_autospec(Message)
        actual = utils.generate_response(message, video)
        message.react.assert_called_once_with(reaction=[ReactionTypeEmoji(emoji="🐳")])
        self.assertIsNotNone(actual)

    def test_too_long_reaction(self):
        video = MagicMock()
        video.invalid_reason = InvalidReason.VIDEO_TOO_LONG
        message = create_autospec(Message)
        actual = utils.generate_response(message, video)
        message.react.assert_called_once_with(reaction=[ReactionTypeEmoji(emoji="🤨")])
        self.assertIsNotNone(actual)

    def test_unsupported_reaction(self):
        video = MagicMock()
        video.invalid_reason = InvalidReason.UNSUPPORTED_URL
        message = create_autospec(Message)
        actual = utils.generate_response(message, video)
        message.react.assert_called_once_with(reaction=[ReactionTypeEmoji(emoji="🤷")])
        self.assertIsNotNone(actual)

    def test_dl_failed_reaction(self):
        video = MagicMock()
        video.invalid_reason = InvalidReason.DOWNLOAD_FAILED
        message = create_autospec(Message)
        actual = utils.generate_response(message, video)
        message.react.assert_called_once_with(reaction=[ReactionTypeEmoji(emoji="😢")])
        self.assertIsNotNone(actual)

    def test_unauthorized_reaction(self):
        video = MagicMock()
        video.invalid_reason = InvalidReason.UNAUTHORIZED
        message = create_autospec(Message)
        actual = utils.generate_response(message, video)
        message.react.assert_called_once_with(reaction=[ReactionTypeEmoji(emoji="🙈")])
        self.assertIsNotNone(actual)

    def test_valid_video(self):
        video = MagicMock()
        video.invalid_reason = None
        video.file_path = "mock/path"
        video.dimensions = (1080, 1920)
        video.duration = 300
        video.description = "Mock description"
        message = create_autospec(Message)
        actual = utils.generate_response(message, video)
        message.reply_video.assert_called_once()
        self.assertIsNotNone(actual)
