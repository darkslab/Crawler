from __future__ import annotations

from asyncio import Queue, TimeoutError
from csv import writer
from io import StringIO
from logging import debug, error, info
from re import DOTALL, IGNORECASE, Match, compile
from typing import Dict, Optional, Pattern, Set, Tuple

from aiohttp import ClientError, ClientResponse, ClientSession, ClientTimeout
from yarl import URL

from .concurrency import ConcurrentMillWorker
from .types import Queable, URLStatistic

DEFAULT_USER_AGENT: str = "Mozilla/5.0 (iPhone; CPU iPhone OS 15_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.2 Mobile/15E148 Safari/604.1"
LINKS_REGEX: Pattern[str] = compile(
    r'<a .*?href="(?P<href>.*?)".*?>.*?</a>', flags=(IGNORECASE | DOTALL)
)


class CrawlerMillWorker(ConcurrentMillWorker[Tuple[URL, URL]]):
    def __init__(self) -> None:
        self._base_url: URL = URL("https://xkcd.com")
        self._session: ClientSession = ClientSession(
            headers={"User-Agent": DEFAULT_USER_AGENT},
            timeout=ClientTimeout(total=60),
            raise_for_status=True,
        )
        self._seen_urls: Set[URL] = set()
        self._stats: Dict[URL, URLStatistic] = {}

    def create_data_queue(self) -> "Queue[Tuple[URL, URL]]":
        queue: Queue[Tuple[URL, URL]] = super().create_data_queue()
        self._add_url(self._base_url, queue)
        return queue

    def max_tasks(self) -> int:
        return 256

    async def coro_process_data(
        self, data: Tuple[URL, URL], queue: Queable[Tuple[URL, URL]]
    ) -> None:
        debug(f"Processing {data[0]}...")

        exception: Exception
        response: ClientResponse
        try:
            async with self._session.get(data[0]) as response:
                page: str = await response.text(encoding="utf-8")
                match: Match
                total: int = 0
                for match in LINKS_REGEX.finditer(page):
                    next_url: Optional[URL] = self._rectified_url(
                        match.group("href"), data[1]
                    )
                    if next_url is None or next_url in self._seen_urls:
                        continue
                    self._add_url(next_url, queue)
                    total += 1
                self._stats[data[0]] = URLStatistic(
                    size=int(response.headers["Content-Length"]),
                    links=total,
                )
        except ClientError as exception:
            error(exception)
        except TimeoutError:
            error(f"Request to {data[0]} timed out")

    async def coro_close(self) -> None:
        await self._session.close()

    def print_summary(self) -> None:
        buffer: StringIO = StringIO()
        # pyre-fixme [6]: In call `_csv.writer`, for 1st positional only parameter expected `_Writer` but got `StringIO`
        csv_writer = writer(buffer)
        url: URL
        stat: URLStatistic

        for url, stat in self._stats.items():
            csv_writer.writerow(
                (
                    url,
                    stat.size,
                    stat.links,
                )
            )
        buffer.seek(0)
        print(buffer.read())

    def _add_url(self, url: URL, queue: Queable[Tuple[URL, URL]]) -> None:
        queue.put_nowait((url, url.parent))
        self._seen_urls.add(url)

    def _rectified_url(self, raw_link: str, parent_url: URL) -> Optional[URL]:
        link: URL = URL(raw_link)
        if link.host is not None and link.host.lower() != self._base_url.host:
            return None
        return parent_url.join(
            URL(
                link.path_qs
                if len(link.path_qs) == 0 or link.path_qs[-1] != "/"
                else link.path_qs[:-1]
            )
        )
