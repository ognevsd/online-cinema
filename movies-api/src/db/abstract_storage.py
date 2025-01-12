from abc import ABC, abstractmethod


class AbstractStorage(ABC):
    @abstractmethod
    async def get_all(
        self, *args, **kwargs
    ) -> tuple[list[dict], int] | tuple[None, None]:
        pass

    @abstractmethod
    async def search(
        self, *args, **kwargs
    ) -> tuple[list[dict], int] | tuple[None, None]:
        pass

    @abstractmethod
    async def get_by_id(self, *args, **kwargs) -> dict | None:
        pass
