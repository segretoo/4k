import asyncio
import json

import pytest

from app.services.gpu_queue import FairGpuQueue, QueueBusy
from app.services.gpu_client import HttpGpu


def test_gpu_queue_is_fifo_and_bounds_each_browser_to_one_waiter():
    async def scenario():
        queue = FairGpuQueue(max_waiting=2)
        started = []
        active = asyncio.Event()
        release = asyncio.Event()

        async def first():
            async with queue.slot("a"):
                started.append("a")
                active.set()
                await release.wait()

        async def later(owner):
            async with queue.slot(owner):
                started.append(owner)

        first_task = asyncio.create_task(first())
        await active.wait()
        second = asyncio.create_task(later("b"))
        await asyncio.sleep(0)
        with pytest.raises(QueueBusy):
            async with queue.slot("b"):
                pass
        third = asyncio.create_task(later("c"))
        await asyncio.sleep(0)
        with pytest.raises(QueueBusy):
            async with queue.slot("d"):
                pass
        release.set()
        await asyncio.gather(first_task, second, third)
        assert started == ["a", "b", "c"]

    asyncio.run(asyncio.wait_for(scenario(), timeout=5))


def test_browser_owner_stays_in_cpu_gateway(monkeypatch):
    async def scenario():
        client = HttpGpu()
        seen = {}

        async def fake_post(path, *, owner_id="", **kwargs):
            seen.update(path=path, owner_id=owner_id, meta=json.loads(kwargs["data"]["meta"]))
            return {"photo_id": "uc2", "texts": [], "entities": [],
                    "risk": {"level": "safe", "why": ""}}

        monkeypatch.setattr(client, "_post", fake_post)
        await client.analyze(b"image", {"photo_id": "uc2", "caption": "test", "owner_id": "secret-session-id"})
        assert seen["owner_id"] == "secret-session-id"  # CPU-side fair-queue key only
        assert "owner_id" not in seen["meta"]

    asyncio.run(scenario())
