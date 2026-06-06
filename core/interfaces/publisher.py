from abc import ABC, abstractmethod
from core.models.post import Post


class AbstractPublisher(ABC):
    @property
    @abstractmethod
    def platform_name(self) -> str: ...

    @abstractmethod
    async def publish(self, post: Post) -> bool: ...
