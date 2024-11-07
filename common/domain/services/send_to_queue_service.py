from abc import ABC, abstractmethod

from common.domain.models import Task


class ISendToQueueService(ABC):
    @abstractmethod
    async def send_message(self, message: dict) -> Task:
        pass
