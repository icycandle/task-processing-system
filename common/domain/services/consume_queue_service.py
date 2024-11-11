from abc import ABC, abstractmethod


class IConsumeQueueService(ABC):
    @abstractmethod
    async def consume(self, message_handler):
        pass
