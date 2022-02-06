from __future__ import annotations

from typing import NamedTuple, Protocol, TypeVar

_T = TypeVar("_T")


class Queable(Protocol[_T]):
    async def put(self, item: _T) -> None:
        pass

    def put_nowait(self, item: _T) -> None:
        pass


class URLStatistic(NamedTuple):
    size: int
    links: int
