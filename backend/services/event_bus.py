"""
SEED AI — Event Bus
Async event-driven message bus with background batch writer.
Decouples the orchestrator from synchronous persistence:
  Orchestrator emits events → EventBus queues them → Background worker
  batches and flushes to Firestore every N seconds or every M events.
"""
import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional

logger = logging.getLogger("EventBus")

PersistenceHandler = Callable[[List[Dict[str, Any]]], Awaitable[None]]


class EventBus:
    """
    In-process async event bus with batched persistence.

    Usage:
        bus = EventBus(flush_interval=2.0, batch_size=50)
        await bus.start()
        await bus.emit({"type": "persist", "payload": {...}})
        # ... background worker flushes every 2s or when batch reaches 50
        await bus.shutdown()
    """

    def __init__(
        self,
        flush_interval: float = 2.0,
        batch_size: int = 50,
        handler: Optional[PersistenceHandler] = None,
    ):
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=5000)
        self._flush_interval = flush_interval
        self._batch_size = batch_size
        self._handler = handler
        self._running = False
        self._consumer_task: Optional[asyncio.Task] = None
        self._subscribers: Dict[str, List[Callable]] = {}
        self._metrics = {"emitted": 0, "flushed": 0, "dropped": 0}

    @property
    def metrics(self) -> Dict[str, Any]:
        return {**self._metrics, "queue_size": self._queue.qsize()}

    async def start(self):
        if self._running:
            return
        self._running = True
        self._consumer_task = asyncio.create_task(self._consumer_loop())
        logger.info(
            f"EventBus started (flush_interval={self._flush_interval}s, "
            f"batch_size={self._batch_size})"
        )

    async def emit(self, event: Dict[str, Any]):
        """
        Emit an event to the bus.
        If the queue is full, the event is dropped and counter incremented.
        """
        try:
            self._queue.put_nowait(event)
            self._metrics["emitted"] += 1
        except asyncio.QueueFull:
            self._metrics["dropped"] += 1
            logger.warning(f"EventBus queue full, event dropped: {event.get('type', 'unknown')}")

    def subscribe(self, event_type: str, callback: Callable):
        """Subscribe to specific event types (for SSE or live updates)."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: Callable):
        if event_type in self._subscribers:
            self._subscribers[event_type] = [
                cb for cb in self._subscribers[event_type] if cb is not callback
            ]

    async def _notify_subscribers(self, event: Dict[str, Any]):
        """Notify any registered callbacks for the event type."""
        event_type = event.get("type", "")
        for callback in self._subscribers.get(event_type, []):
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"EventBus subscriber error: {e}")

    async def _consumer_loop(self):
        """Background loop: accumulates events and flushes them in batches."""
        batch: List[Dict[str, Any]] = []

        while self._running:
            try:
                event = await asyncio.wait_for(
                    self._queue.get(), timeout=self._flush_interval
                )
                batch.append(event)
                await self._notify_subscribers(event)

                # Drain any additional events available immediately
                while len(batch) < self._batch_size:
                    try:
                        event = self._queue.get_nowait()
                        batch.append(event)
                        await self._notify_subscribers(event)
                    except asyncio.QueueEmpty:
                        break

                if len(batch) >= self._batch_size:
                    await self._flush(batch)
                    batch.clear()

            except asyncio.TimeoutError:
                if batch:
                    await self._flush(batch)
                    batch.clear()

        # Final flush on shutdown
        if batch:
            await self._flush(batch)

    async def _flush(self, batch: List[Dict[str, Any]]):
        """Flush a batch of events using the registered handler or default."""
        self._metrics["flushed"] += len(batch)
        if self._handler:
            try:
                await self._handler(batch)
            except Exception as e:
                logger.error(f"EventBus handler error: {e}")
        else:
            logger.debug(f"EventBus flush: {len(batch)} events (no handler registered)")

    async def shutdown(self):
        """Graceful shutdown — flush remaining events and stop consumer."""
        logger.info("EventBus shutting down...")
        self._running = False
        if self._consumer_task:
            try:
                await asyncio.wait_for(self._consumer_task, timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning("EventBus consumer did not finish in time, cancelling")
                self._consumer_task.cancel()
        logger.info(
            f"EventBus stopped. Metrics: {self._metrics}"
        )
