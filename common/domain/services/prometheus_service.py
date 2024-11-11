from abc import ABC, abstractmethod


class IPrometheusMetricsService(ABC):

    @abstractmethod
    async def inc_label(self, label: str):
        pass

    @abstractmethod
    def observe_processing_time(self, duration: float):
        pass

    @abstractmethod
    def observe_execution_time(self, duration: float):
        pass
