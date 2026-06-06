from abc import ABC, abstractmethod
from typing import List


class AbstractImageProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @abstractmethod
    async def find_image(self, keywords: List[str]) -> str | None: ...
