import logging

from aiogram.enums import MessageEntityType
from aiogram.filters import Filter
from aiogram.types import Message


class EntityTypeFilter(Filter):
    """ """

    def __init__(self, filter_type: MessageEntityType):
        self.log = logging.getLogger(__name__)
        self.filter_type = filter_type

    async def __call__(self, message: Message) -> bool:
        if message.entities is None:
            return False
        else:
            self.log.debug(message.entities)
            return any([self.filter_type in entity.type for entity in message.entities])
