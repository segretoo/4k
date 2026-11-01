"""Fair, bounded, single-flight admission for calls to the one GPU model worker."""
import asyncio
from collections import deque
from contextlib import asynccontextmanager
import secrets


class QueueBusy(RuntimeError):
    """The caller already owns a slot or the shared waiting queue is full."""


class FairGpuQueue:
    def __init__(self, max_waiting: int = 4) -> None:
        self.max_waiting = max_waiting
        self._condition = asyncio.Condition()
        self._waiting: deque[str] = deque()
        self._active: str | None = None

    @property
    def waiting(self) -> int:
        return len(self._waiting)

    @asynccontextmanager
    async def slot(self, owner_id: str):
        owner = owner_id or f"internal:{secrets.token_hex(16)}"
        queued = False
        async with self._condition:
            if owner in self._waiting:
                raise QueueBusy("this browser already has a waiting GPU request")
            if self._active is None and not self._waiting:
                self._active = owner
            else:
                if len(self._waiting) >= self.max_waiting:
                    raise QueueBusy("GPU waiting queue is full")
                self._waiting.append(owner)
                queued = True
                try:
                    while self._active is not None or self._waiting[0] != owner:
                        await self._condition.wait()
                    self._waiting.popleft()
                    self._active = owner
                    queued = False
                except BaseException:
                    if queued:
                        self._waiting.remove(owner)
                        self._condition.notify_all()
                    raise
        try:
            yield
        finally:
            async with self._condition:
                self._active = None
                self._condition.notify_all()


gpu_queue = FairGpuQueue(max_waiting=4)
