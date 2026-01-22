import logging

from aiogram.enums import MessageEntityType
from aiogram.filters import Filter
from aiogram.types import Message

logger = logging.getLogger(__name__)


class EntityTypeFilter(Filter):
    def __init__(self, filter_type: MessageEntityType):
        self.filter_type = filter_type

    async def __call__(self, message: Message) -> bool:
        if message.entities is None:
            return False
        else:
            logger.debug(message.entities)
            return any([self.filter_type in entity.type for entity in message.entities])
