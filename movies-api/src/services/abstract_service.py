from abc import ABC, abstractmethod
from pydantic import BaseModel


class AbstractService(ABC):
    @abstractmethod
    async def get_by_id(self, *args, **kwargs) -> BaseModel | None:
        pass

    @abstractmethod
    async def get_all(self, *args, **kwargs) -> tuple[list[BaseModel], int]:
        pass

    @abstractmethod
    async def search(self, *args, **kwargs) -> tuple[list[BaseModel], int]:
        pass
