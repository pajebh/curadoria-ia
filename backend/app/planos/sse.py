import asyncio
import json
from collections.abc import AsyncGenerator


class SSEManager:
    def __init__(self) -> None:
        self._queues: dict[str, asyncio.Queue[dict | None]] = {}

    def create(self, plan_id: str) -> asyncio.Queue[dict | None]:
        q: asyncio.Queue[dict | None] = asyncio.Queue()
        self._queues[plan_id] = q
        return q

    def publish(self, plan_id: str, event: dict | None) -> None:
        q = self._queues.get(plan_id)
        if q is not None:
            q.put_nowait(event)

    def remove(self, plan_id: str) -> None:
        self._queues.pop(plan_id, None)

    async def subscribe(self, plan_id: str) -> AsyncGenerator[str, None]:
        q = self._queues.get(plan_id)
        if q is None:
            yield "event: done\ndata: {}\n\n"
            return
        try:
            while True:
                try:
                    event = await asyncio.wait_for(q.get(), timeout=25.0)
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
                    continue
                if event is None:
                    break
                event_name = event.get("event", "message")
                data = json.dumps({k: v for k, v in event.items() if k != "event"})
                yield f"event: {event_name}\ndata: {data}\n\n"
                if event_name in ("done", "erro"):
                    break
        finally:
            self.remove(plan_id)


sse_manager = SSEManager()
