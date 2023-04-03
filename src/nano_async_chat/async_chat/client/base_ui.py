import logging
import trio
from abc import ABC, abstractmethod


logger = logging.getLogger('client-logger')


class BaseUI(ABC):
    @abstractmethod
    async def command_handler(self, send_channel: trio.MemorySendChannel) -> str:
        pass
