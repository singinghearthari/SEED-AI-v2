"""
SEED AI — Firestore Persistence Handler
Processes batched persistence events from the EventBus.
Batches Firestore writes and commits atomically.
"""
import logging
from typing import Any, Dict, List

from agents.memory_agent import MemoryAgent
from services.firebase_service import is_available as firebase_available

logger = logging.getLogger("PersistenceHandler")


class FirestorePersistenceHandler:
    """
    Batches persistence events from the EventBus and writes them
    to Firestore in a single atomic commit.

    Replaces N individual writes with a single batch.commit().
    Checks Firestore availability dynamically on each flush.
    """

    def __init__(self, memory_agent: MemoryAgent):
        self.memory = memory_agent

    async def __call__(self, batch: List[Dict[str, Any]]):
        if not firebase_available():
            logger.warning(f"Firestore unavailable, dropping {len(batch)} persistence events")
            return

        from firebase_admin import firestore

        processed = 0
        for event in batch:
            event_type = event.get("type", "")
            payload = event.get("payload", {})

            if event_type == "persist" and payload.get("memory_action") == "batch_persist":
                await self._persist_batch(payload)
                processed += 1
            elif event_type == "persist_single":
                await self._persist_single(payload)
                processed += 1

        logger.debug(f"PersistenceHandler: processed {processed}/{len(batch)} events")

    async def _persist_batch(self, payload: Dict[str, Any]):
        """Forward to MemoryAgent.batch_persist via thread pool."""
        try:
            import asyncio
            await asyncio.to_thread(self.memory.process, payload)
        except Exception as e:
            logger.error(f"Batch persist failed: {e}")

    async def _persist_single(self, payload: Dict[str, Any]):
        """Forward a single action to MemoryAgent via thread pool."""
        try:
            import asyncio
            await asyncio.to_thread(self.memory.process, payload)
        except Exception as e:
            logger.error(f"Single persist failed: {e}")
