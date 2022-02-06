from asyncio import run
from logging import basicConfig

from .concurrency import ConcurrentMill
from .mill_workers import CrawlerMillWorker

basicConfig(
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


async def coro_crawler() -> None:
    worker: CrawlerMillWorker
    # pyre-fixme [9]: worker is declared to have type `CrawlerMillWorker` but is used as type `ConcurrentMillWorker[str]`
    async with ConcurrentMill(CrawlerMillWorker()) as worker:
        worker.print_summary()


def cli() -> None:
    run(coro_crawler())
