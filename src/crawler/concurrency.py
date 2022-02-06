from __future__ import annotations

from abc import ABC, abstractmethod
from asyncio import CancelledError, Queue, Task, create_task
from collections.abc import Collection
from logging import debug
from typing import Generic, List, Optional, TypeVar
from warnings import warn

from .types import Queable

_T = TypeVar("_T")


class ConcurrentMill(Generic[_T]):
    def __init__(self, worker: "ConcurrentMillWorker[_T]") -> None:
        self._worker: ConcurrentMillWorker[_T] = worker

        self._queue: Queue[_T] = self._worker.create_data_queue()
        self._tasks: List[Task[None]] = []

    async def _coro_task(self) -> None:
        try:
            while True:
                data: _T = await self._queue.get()
                exception: Exception
                try:
                    await self._worker.coro_process_data(data, self._queue)
                except Exception as exception:
                    task: Optional[Task] = Task.current_task()
                    task_name = (
                        task.get_name() if task is not None else "(Unknown task)"
                    )
                    warn(
                        f"Caught unhandled exception in {task_name} (it has to be handled by client developer): {exception}"
                    )
                finally:
                    self._queue.task_done()
        except CancelledError:
            pass

    async def __aenter__(self) -> "ConcurrentMillWorker[_T]":
        self._tasks.extend(
            create_task(self._coro_task()) for _ in range(self._worker.max_tasks())
        )
        debug(
            f"Created {self._worker.max_tasks()} tasks, now waiting for them to finish"
        )
        await self._queue.join()
        debug("All tasks are done processing")
        return self._worker

    async def __aexit__(self, *args: Collection) -> None:
        await self._worker.coro_close()
        try:
            while True:
                self._tasks.pop().cancel()
        except IndexError:
            debug("All tasks were cancelled")


class ConcurrentMillWorker(Generic[_T], ABC):
    @abstractmethod
    def create_data_queue(self) -> "Queue[_T]":
        return Queue()

    def max_tasks(self) -> int:
        return 1

    @abstractmethod
    async def coro_process_data(self, data: _T, queue: Queable[_T]) -> None:
        pass

    async def coro_close(self) -> None:
        pass
