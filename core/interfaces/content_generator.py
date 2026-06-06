from abc import ABC, abstractmethod
from typing import List
from core.models.raw_content import RawContent
from core.models.post import Post


class AbstractContentGenerator(ABC):
    @property
    @abstractmethod
    def post_type(self) -> str: ...

    @abstractmethod
    async def generate(self, raw_contents: List[RawContent]) -> List[Post]: ...
