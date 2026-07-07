"""
SEED AI — EventBus Singleton
Central singleton access point for the async EventBus.
Initialized by main.py on startup.
"""
from services.event_bus import EventBus
from services.persistence_handler import FirestorePersistenceHandler
from agents.memory_agent import MemoryAgent

_bus: EventBus | None = None


def get_bus() -> EventBus:
    global _bus
    if _bus is None:
        raise RuntimeError("EventBus not initialized. Call init_bus() first.")
    return _bus


def init_bus(memory: MemoryAgent, flush_interval: float = 2.0, batch_size: int = 50) -> EventBus:
    global _bus
    handler = FirestorePersistenceHandler(memory)
    _bus = EventBus(flush_interval=flush_interval, batch_size=batch_size, handler=handler)
    return _bus


def is_initialized() -> bool:
    return _bus is not None
