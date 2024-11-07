from abc import ABC, abstractmethod

import aio_pika


class IConsumeQueueService(ABC):
    @abstractmethod
    async def consume(self):
        pass

    @abstractmethod
    async def process_message(self, message: aio_pika.IncomingMessage):
        pass
