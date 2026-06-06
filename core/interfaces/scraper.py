from abc import ABC, abstractmethod
from typing import List
from core.models.raw_content import RawContent


class AbstractScraper(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    async def scrape(self) -> List[RawContent]: ...
