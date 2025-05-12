import logging
from os import environ
from sys import stdout

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.utils.chat_action import ChatActionMiddleware

from vidfetch_bot.handlers import handle

logging.basicConfig(
    level=logging.INFO,
    stream=stdout,
    format="%(asctime)s %(name)s %(levelname)s: %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
)

bot_token = environ["BOT_TOKEN"]
dp = Dispatcher()
dp.message.middleware(ChatActionMiddleware())
bot = Bot(token=bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

def start():
    dp.include_router(handle)
    dp.run_polling(bot)