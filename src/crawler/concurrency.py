from __future__ import annotations

from abc import ABC, abstractmethod
from asyncio import CancelledError, Queue, Task, create_task, current_task
from logging import info
from typing import Generic, List, Optional, TypeVar
from warnings import warn

from .types import Queable

_T = TypeVar("_T")


class AsyncQueueProcessor(Generic[_T], ABC):
    @abstractmethod
    def create_data_queue(self) -> Queue[_T]:
        pass

    @abstractmethod
    def max_tasks(self) -> int:
        pass

    @abstractmethod
    async def coro_process_data(self, data: _T, queue: Queable[_T]) -> None:
        pass


async def coro_process_queue(queue_processor: AsyncQueueProcessor[_T]) -> None:
    queue: Queue[_T] = queue_processor.create_data_queue()
    info(f"Received a queue with size ~{queue.qsize()}")

    tasks: List[Task[None]] = [
        create_task(_coro_task(queue, queue_processor))
        for _ in range(queue_processor.max_tasks())
    ]
    info(f"Created {len(tasks)} asynchronous tasks")

    await queue.join()
    info("All tasks are done processing and queue is empty")

    while len(tasks) > 0:
        tasks.pop().cancel()
    info("All tasks were cancelled")


async def _coro_task(
    queue: Queue[_T], queue_processor: AsyncQueueProcessor[_T]
) -> None:
    try:
        while True:
            data: _T = await queue.get()
            exception: Exception
            try:
                await queue_processor.coro_process_data(data, queue)
            except Exception as exception:
                task: Optional[Task] = current_task()
                task_name = task.get_name() if task is not None else "(Unknown task)"
                warn(
                    f"Caught unhandled exception in {task_name} (it has to be handled by client developer): {exception}"
                )
            finally:
                queue.task_done()
    except CancelledError:
        pass
