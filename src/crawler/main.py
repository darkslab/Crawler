from asyncio import run
from logging import basicConfig

from .concurrency import coro_process_queue
from .queue_processors import CrawlerQueueProcessor

basicConfig(
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


async def coro_crawler() -> None:
    processor: CrawlerQueueProcessor
    async with CrawlerQueueProcessor() as processor:
        await coro_process_queue(processor)
        processor.print_summary_csv()


def cli() -> None:
    run(coro_crawler())
